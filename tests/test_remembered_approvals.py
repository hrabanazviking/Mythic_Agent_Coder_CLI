"""M-096 Remembered approvals with scope - pure-layer tests.

TIER: integration

Scopes are exact in all three parts (command + args
pattern + path), nothing is remembered silently,
the list is the whole truth in one screen, and
revocation names the id the screen shows.
"""

import pytest

from mythic_agent.core.remembered_approvals import (
    PLAIN_EXPLANATION,
    SETTING_KEY,
    approval_change_record,
    args_match,
    find_match,
    format_remembered_approval,
    format_remembered_approvals,
    matches,
    normalize_path,
    parse_remember_args,
    remember_approval,
    revoke_approval,
    scope_fingerprint,
    stored_approvals,
    validate_record,
    validate_scope,
)

SPEC = {"command": "git", "args_pattern": ["status"], "path": "/home/u/proj"}
WILD = {"command": "git", "args_pattern": ["*"], "path": "/home/u/proj"}
OTHER = {"command": "pytest", "args_pattern": ["-q"], "path": "/home/u/proj"}


def remembered(*specs):
    out = []
    for spec in specs:
        out = remember_approval(out, spec, explicit=True)
    return out


# -- scope validation ---------------------------------------------------


def test_scope_validates_and_normalizes_path():
    scope = validate_scope(
        {"command": " git ", "args_pattern": ["status"], "path": "./proj/"}
    )
    assert scope.command == "git"
    assert scope.args_pattern == ("status",)
    assert scope.path == "proj"


def test_normalize_path_spellings():
    assert normalize_path("/a/b/") == "/a/b"
    assert normalize_path("a\\b") == "a/b"
    assert normalize_path("/") == "/"
    with pytest.raises(ValueError):
        normalize_path("  ")


def test_scope_refuses_wildcard_command():
    with pytest.raises(ValueError):
        validate_scope({"command": "*", "args_pattern": [], "path": "/p"})
    with pytest.raises(ValueError):
        validate_scope({"command": "gi?", "args_pattern": [], "path": "/p"})


def test_scope_refuses_command_with_spaces():
    with pytest.raises(ValueError):
        validate_scope(
            {"command": "git status", "args_pattern": [], "path": "/p"}
        )


def test_scope_refuses_unknown_and_missing_keys():
    with pytest.raises(ValueError):
        validate_scope(
            {"command": "git", "args_pattern": [], "path": "/p", "x": 1}
        )
    with pytest.raises(ValueError):
        validate_scope({"command": "git", "args_pattern": []})


def test_scope_refuses_bad_args_pattern():
    with pytest.raises(ValueError):
        validate_scope({"command": "git", "args_pattern": "status", "path": "/p"})
    with pytest.raises(ValueError):
        validate_scope({"command": "git", "args_pattern": [""], "path": "/p"})
    with pytest.raises(ValueError):
        validate_scope({"command": "git", "args_pattern": [3], "path": "/p"})


def test_empty_args_pattern_is_valid():
    scope = validate_scope({"command": "pwd", "args_pattern": [], "path": "/p"})
    assert scope.args_pattern == ()


def test_fingerprint_is_stable_and_scope_bound():
    a = validate_scope(SPEC)
    b = validate_scope(dict(SPEC))
    c = validate_scope(OTHER)
    assert scope_fingerprint(a) == scope_fingerprint(b)
    assert scope_fingerprint(a) != scope_fingerprint(c)
    assert len(scope_fingerprint(a)) == 64


# -- exact matching -------------------------------------------------------


def test_args_match_exact_and_wildcard():
    assert args_match(("status",), ["status"]) is True
    assert args_match(("*",), ["status"]) is True
    assert args_match(("*", "*"), ["a", "b"]) is True
    assert args_match(("status",), ["log"]) is False
    assert args_match(("*",), ["a", "b"]) is False
    assert args_match((), []) is True
    assert args_match((), ["x"]) is False


def test_matches_needs_all_three_parts_exact():
    (approval,) = remembered(SPEC)
    assert matches(approval, "git", ["status"], "/home/u/proj") is True
    assert matches(approval, "git", ["status"], "/home/u/proj/") is True
    assert matches(approval, "git", ["log"], "/home/u/proj") is False
    assert matches(approval, "git", ["status", "-s"], "/home/u/proj") is False
    assert matches(approval, "hg", ["status"], "/home/u/proj") is False
    assert matches(approval, "git", ["status"], "/home/u/other") is False
    # no prefix / substring broadening
    assert matches(approval, "git", ["stat"], "/home/u/proj") is False
    assert matches(approval, "git", ["status"], "/home/u/proj/sub") is False


def test_find_match_none_and_hit():
    approvals = remembered(SPEC, OTHER)
    assert find_match(approvals, "git", ["status"], "/home/u/proj").command == "git"
    assert find_match(approvals, "git", ["push"], "/home/u/proj") is None
    assert find_match([], "git", ["status"], "/home/u/proj") is None


def test_find_match_prefers_fewest_wildcards():
    approvals = remembered(WILD, SPEC)
    hit = find_match(approvals, "git", ["status"], "/home/u/proj")
    assert hit.args_pattern == ("status",)
    hit2 = find_match(approvals, "git", ["log"], "/home/u/proj")
    assert hit2.args_pattern == ("*",)


# -- remembering: never silently -----------------------------------------


def test_remember_requires_explicit_true():
    with pytest.raises(ValueError):
        remember_approval([], SPEC)
    with pytest.raises(ValueError):
        remember_approval([], SPEC, explicit=False)
    with pytest.raises(ValueError):
        remember_approval([], SPEC, explicit="yes")
    out = remember_approval([], SPEC, explicit=True)
    assert len(out) == 1 and out[0].command == "git"


def test_remember_duplicate_refuses():
    approvals = remembered(SPEC)
    with pytest.raises(ValueError):
        remember_approval(approvals, SPEC, explicit=True)
    # same scope in a different path spelling is still a duplicate
    with pytest.raises(ValueError):
        remember_approval(
            approvals,
            {"command": "git", "args_pattern": ["status"], "path": "/home/u/proj/"},
            explicit=True,
        )


def test_remember_does_not_mutate_the_old_list():
    before = remembered(SPEC)
    after = remember_approval(before, OTHER, explicit=True)
    assert len(before) == 1 and len(after) == 2


# -- stored list ------------------------------------------------------------


def test_stored_absent_is_empty():
    assert stored_approvals({}) == []
    assert stored_approvals({SETTING_KEY: []}) == []


def test_stored_round_trip():
    approvals = remembered(SPEC, OTHER)
    config = {SETTING_KEY: [a.scope.to_record() for a in approvals]}
    back = stored_approvals(config)
    assert [a.id for a in back] == [a.id for a in approvals]


def test_stored_malformed_raises():
    with pytest.raises(ValueError):
        stored_approvals({SETTING_KEY: "git status"})
    with pytest.raises(ValueError):
        stored_approvals({SETTING_KEY: [{"command": "git"}]})
    with pytest.raises(ValueError):
        stored_approvals({SETTING_KEY: [dict(SPEC), dict(SPEC)]})
    with pytest.raises(ValueError):
        stored_approvals({SETTING_KEY: [dict(SPEC, extra=1)]})


def test_record_id_must_agree_with_scope():
    (approval,) = remembered(SPEC)
    record = approval.to_record()
    assert validate_record(record).id == approval.id
    bad = dict(record, id="0" * 64)
    with pytest.raises(ValueError):
        validate_record(bad)
    with pytest.raises(ValueError):
        validate_record(dict(record, type="something_else"))


# -- revocation -------------------------------------------------------------


def test_revoke_by_full_id_and_unique_prefix():
    approvals = remembered(SPEC, OTHER)
    target = approvals[0]
    out = revoke_approval(approvals, target.id)
    assert [a.id for a in out] == [approvals[1].id]
    out2 = revoke_approval(approvals, target.id[:8])
    assert [a.id for a in out2] == [approvals[1].id]
    assert len(approvals) == 2  # old list untouched


def test_revoke_unknown_and_short_refuse():
    approvals = remembered(SPEC)
    with pytest.raises(ValueError):
        revoke_approval(approvals, "zzzzzz")
    with pytest.raises(ValueError):
        revoke_approval(approvals, approvals[0].id[:5])
    with pytest.raises(ValueError):
        revoke_approval(approvals, "")


# -- listing + records + grammar -------------------------------------------


def test_listing_empty_and_full():
    assert "No remembered approvals" in format_remembered_approvals([])
    approvals = remembered(SPEC, OTHER)
    text = format_remembered_approvals(approvals)
    assert "Remembered approvals (2):" in text
    assert "git status in /home/u/proj" in text
    assert "pytest -q in /home/u/proj" in text
    for a in approvals:
        assert a.id[:12] in text


def test_format_one_line_and_no_args():
    (approval,) = remembered({"command": "pwd", "args_pattern": [], "path": "/p"})
    line = format_remembered_approval(approval)
    assert line.startswith("pwd (no args) in /p [")


def test_change_record_shape():
    (approval,) = remembered(SPEC)
    record = approval_change_record("remembered", approval, total=1)
    assert record["type"] == "remembered_approval"
    assert record["action"] == "remembered"
    assert record["total"] == 1
    assert record["id"] == approval.id
    with pytest.raises(ValueError):
        approval_change_record("forgot", approval, total=0)


def test_parse_remember_args():
    assert parse_remember_args("") == {"action": "list"}
    assert parse_remember_args("list") == {"action": "list"}
    assert parse_remember_args("show") == {"action": "list"}
    assert parse_remember_args("clear") == {"action": "clear"}
    assert parse_remember_args("forget abc123") == {
        "action": "forget",
        "id": "abc123",
    }
    with pytest.raises(ValueError):
        parse_remember_args("forget")
    with pytest.raises(ValueError):
        parse_remember_args("always git")


def test_plain_explanation_names_the_rules():
    assert "exact scope" in PLAIN_EXPLANATION
    assert "revoked" in PLAIN_EXPLANATION


# -- agent layer: status, remember, revoke, clear, consult (M-096) -----

from mythic_agent.core import remembered_approvals as ra
from mythic_agent.core.sessions import SessionStore


def _store_for(tmp_path):
    return SessionStore(tmp_path, tmp_path / "state")


class TestRememberedApprovalAgent:
    def test_status_empty_by_default(self, agent):
        status = agent.remembered_approvals_status()
        assert status["approvals"] == []
        assert status["count"] == 0
        assert "No remembered approvals" in status["screen"]
        assert status["explanation"] == ra.PLAIN_EXPLANATION

    def test_remember_explicit_stores_plain_scope_records(self, agent):
        record = agent.remember_command_approval(SPEC, explicit=True)
        assert record["type"] == "remembered_approval"
        assert record["action"] == "remembered"
        assert record["total"] == 1
        assert record["journaled"] is False
        assert agent.config[ra.SETTING_KEY] == [dict(SPEC)]
        status = agent.remembered_approvals_status()
        assert status["count"] == 1
        assert status["approvals"][0]["id"] == record["id"]
        assert "git status in /home/u/proj" in status["screen"]

    def test_remember_without_explicit_refuses_and_stores_nothing(
            self, agent):
        with pytest.raises(ValueError, match="nothing is remembered silently"):
            agent.remember_command_approval(SPEC)
        with pytest.raises(ValueError):
            agent.remember_command_approval(SPEC, explicit="yes")
        assert ra.SETTING_KEY not in agent.config

    def test_remember_duplicate_refuses(self, agent):
        agent.remember_command_approval(SPEC, explicit=True)
        with pytest.raises(ValueError, match="already remembered"):
            agent.remember_command_approval(SPEC, explicit=True)
        assert agent.remembered_approvals_status()["count"] == 1

    def test_remember_second_scope_appends_in_order(self, agent):
        agent.remember_command_approval(SPEC, explicit=True)
        record = agent.remember_command_approval(OTHER, explicit=True)
        assert record["total"] == 2
        status = agent.remembered_approvals_status()
        assert [a["command"] for a in status["approvals"]] == [
            "git", "pytest"]

    def test_remember_journals_on_the_session(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.remember_command_approval(SPEC, explicit=True)
        assert record["journaled"] is True
        events = [e for e in store.export(session_id)["events"]
                  if e["type"] == "remembered_approval"]
        assert len(events) == 1
        assert events[0]["action"] == "remembered"
        assert events[0]["total"] == 1
        agent.close()

    def test_remember_save_failure_reverts_and_journals(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.remember_command_approval(SPEC, explicit=True)
        assert ra.SETTING_KEY not in agent.config
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["remembered_approval",
                              "remembered_approval_reverted"]
        agent.close()

    def test_status_and_check_raise_on_malformed_stored_data(self, agent):
        agent.config[ra.SETTING_KEY] = "git status"
        with pytest.raises(ValueError):
            agent.remembered_approvals_status()
        with pytest.raises(ValueError):
            agent.remembered_approval_for(
                "git", ["status"], "/home/u/proj")

    def test_revoke_by_unique_prefix_removes_exactly_one(self, agent):
        agent.remember_command_approval(SPEC, explicit=True)
        agent.remember_command_approval(OTHER, explicit=True)
        target = agent.remembered_approvals_status()["approvals"][0]
        record = agent.revoke_remembered_approval(target["id"][:8])
        assert record["action"] == "revoked"
        assert record["total"] == 1
        status = agent.remembered_approvals_status()
        assert [a["command"] for a in status["approvals"]] == ["pytest"]

    def test_revoke_unknown_id_refuses_and_removes_nothing(self, agent):
        agent.remember_command_approval(SPEC, explicit=True)
        with pytest.raises(ValueError, match="no remembered approval"):
            agent.revoke_remembered_approval("zzzzzz")
        assert agent.remembered_approvals_status()["count"] == 1

    def test_revoke_save_failure_preserves_and_journals(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        agent.remember_command_approval(SPEC, explicit=True)
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        target = agent.remembered_approvals_status()["approvals"][0]
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.revoke_remembered_approval(target["id"])
        assert agent.remembered_approvals_status()["count"] == 1
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["remembered_approval",
                              "remembered_approval_reverted"]
        agent.close()

    def test_clear_removes_all_and_journals(self, agent, tmp_path):
        agent.remember_command_approval(SPEC, explicit=True)
        agent.remember_command_approval(OTHER, explicit=True)
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.clear_remembered_approvals()
        assert record["cleared"] == 2
        assert record["total"] == 0
        assert record["journaled"] is True
        assert agent.config[ra.SETTING_KEY] == []
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "remembered_approvals_cleared" in types
        agent.close()

    def test_clear_empty_is_a_plain_noop(self, agent):
        record = agent.clear_remembered_approvals()
        assert record["cleared"] == 0
        assert record["journaled"] is False
        assert agent.config.get(ra.SETTING_KEY) in (None, [])

    def test_clear_save_failure_preserves(self, agent, monkeypatch):
        from mythic_agent.agents import llm

        agent.remember_command_approval(SPEC, explicit=True)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.clear_remembered_approvals()
        assert agent.remembered_approvals_status()["count"] == 1

    def test_check_consults_the_exact_scope(self, agent):
        agent.remember_command_approval(SPEC, explicit=True)
        agent.remember_command_approval(WILD, explicit=True)
        hit = agent.remembered_approval_for(
            "git", ["status"], "/home/u/proj")
        assert hit is not None and hit.args_pattern == ("status",)
        wild = agent.remembered_approval_for(
            "git", ["log"], "/home/u/proj")
        assert wild is not None and wild.args_pattern == ("*",)
        assert agent.remembered_approval_for(
            "git", ["status"], "/home/u/other") is None
        assert agent.remembered_approval_for(
            "hg", ["status"], "/home/u/proj") is None
        assert agent.remembered_approval_for(
            "git", ["status", "-s"], "/home/u/proj") is None

    def test_allows_tool_only_for_run_command_exact(self, agent):
        spec = {"command": "git", "args_pattern": ["status"],
                "path": str(agent.project_root)}
        agent.remember_command_approval(spec, explicit=True)
        assert agent.remembered_approval_allows_tool(
            "run_command", {"command": "git status"}) is True
        assert agent.remembered_approval_allows_tool(
            "run_command", {"command": "git log"}) is False
        assert agent.remembered_approval_allows_tool(
            "run_command", {"command": "git status -s"}) is False
        assert agent.remembered_approval_allows_tool(
            "write_file", {"command": "git status"}) is False
        assert agent.remembered_approval_allows_tool(
            "run_command", {}) is False
        assert agent.remembered_approval_allows_tool(
            "run_command", {"command": "git 'status"}) is False

    def test_live_ask_road_consults_remembered_first(self, agent):
        from mythic_agent.core.policy import ToolPolicy

        spec = {"command": "git", "args_pattern": ["status"],
                "path": str(agent.project_root)}
        agent.remember_command_approval(spec, explicit=True)
        agent.bind_tui(object(), mode="ask")
        assert isinstance(agent.tool_policy, ToolPolicy)
        # The remembered scope answers without the prompt road:
        # the stand-in app cannot approve anything at all.
        assert agent.tool_policy.authorize(
            "run_command", {"command": "git status"}) is True
        assert agent.tool_policy.authorize(
            "run_command", {"command": "git log"}) is False
        assert agent.tool_policy.denials == ["run_command"]


class TestRememberTerminalSurface:
    def test_list_empty_screen(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/remember")
        assert "Remembered approvals (M-096)" in text
        assert "No remembered approvals" in text
        assert "Usage: /remember" in text
        assert "never creates one" in text

    def test_list_shows_every_remembered_approval(self, agent):
        from mythic_agent.terminal import _slash

        agent.remember_command_approval(SPEC, explicit=True)
        agent.remember_command_approval(OTHER, explicit=True)
        _, _, text = _slash(agent, "/remember list")
        assert "Remembered approvals (2):" in text
        assert "git status in /home/u/proj" in text
        assert "pytest -q in /home/u/proj" in text

    def test_forget_via_terminal(self, agent):
        from mythic_agent.terminal import _slash

        agent.remember_command_approval(SPEC, explicit=True)
        target = agent.remembered_approvals_status()["approvals"][0]
        _, _, text = _slash(
            agent, f"/remember forget {target['id'][:8]}")
        assert "Revoked remembered approval: git status" in text
        assert agent.remembered_approvals_status()["count"] == 0

    def test_clear_via_terminal(self, agent):
        from mythic_agent.terminal import _slash

        agent.remember_command_approval(SPEC, explicit=True)
        agent.remember_command_approval(OTHER, explicit=True)
        _, _, text = _slash(agent, "/remember clear")
        assert "Cleared 2 remembered approval(s)" in text
        assert agent.remembered_approvals_status()["count"] == 0

    def test_unknown_verb_is_the_usage_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/remember always git")
        assert text == ra.USAGE

    def test_forget_unknown_id_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/remember forget zzzzzz")
        assert "no remembered approval carries that id" in text

    def test_terminal_policy_consults_remembered_first(
            self, agent, tmp_path):
        from types import SimpleNamespace

        from mythic_agent import terminal
        from mythic_agent.core.secure_api import unsubscribe

        args = SimpleNamespace(workspace=tmp_path, model=None,
                               base_url=None, permission="ask",
                               resume=None)
        wired = terminal.configured_agent(args, "ask")
        try:
            spec = {"command": "git", "args_pattern": ["status"],
                    "path": str(wired.project_root)}
            wired.remember_command_approval(spec, explicit=True)
            # _approve refuses on a non-tty; only the remembered
            # scope can answer True here.
            assert wired.tool_policy.authorize(
                "run_command", {"command": "git status"}) is True
            assert wired.tool_policy.authorize(
                "run_command", {"command": "git log"}) is False
        finally:
            wired.close()
            unsubscribe("agent_clear_history",
                        wired._handle_clear_history)
            unsubscribe("agent_compact_history",
                        wired._handle_compact_history)


@pytest.fixture()
def remember_handler(agent, monkeypatch):
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


def _remember_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestRememberCommand:
    def test_show_is_default(self, remember_handler, agent):
        remember_handler._handle_remember("")
        text = _remember_published_text(remember_handler)
        assert "Remembered approvals (M-096)" in text
        assert "No remembered approvals" in text

    def test_forget_via_the_handler(self, remember_handler, agent):
        agent.remember_command_approval(SPEC, explicit=True)
        target = agent.remembered_approvals_status()["approvals"][0]
        remember_handler._handle_remember(f"forget {target['id'][:8]}")
        assert "Revoked remembered approval: git status" in (
            _remember_published_text(remember_handler))
        assert agent.remembered_approvals_status()["count"] == 0

    def test_clear_via_the_handler(self, remember_handler, agent):
        agent.remember_command_approval(SPEC, explicit=True)
        remember_handler._handle_remember("clear")
        assert "Cleared 1 remembered approval(s)" in (
            _remember_published_text(remember_handler))
        assert agent.remembered_approvals_status()["count"] == 0

    def test_unknown_verb_is_published(self, remember_handler, agent):
        remember_handler._handle_remember("always git")
        assert ra.USAGE in _remember_published_text(remember_handler)
