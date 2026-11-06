"""M-099 Path jail - pure-layer tests.

TIER: integration

The pure layer is one mechanical judge for one
candidate path: resolve it against the workspace
when relative, resolve every symlink with
realpath, then allow only inside the workspace
root or a named grant root - everything else is
refused by default (fail-closed). Symlink escapes,
``..`` traversal and sibling-prefix tricks are
pinned here with REAL directories and REAL
symlinks on disk.
"""

import os

import pytest

from mythic_agent.core.path_jail import (
    DECISIONS,
    DEFAULT_DECISION,
    GRANTS_KEY,
    PATH_JAIL_SLICE,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    USAGE,
    JailRefusal,
    PathJail,
    build_grants,
    build_refusal,
    check_path,
    decide_path,
    enabled_from_config,
    format_gate_change,
    format_grants,
    format_jail_decision,
    format_path_jail,
    format_refusal,
    grants_from_config,
    is_within,
    jail_from_config,
    normalize_grant,
    parse_pathjail_args,
    refusal_record,
    resolve_workspace_root,
    set_enabled,
    validate_grant,
)


@pytest.fixture()
def layout(tmp_path):
    ws = tmp_path / "ws"
    (ws / "sub").mkdir(parents=True)
    (ws / "notes.txt").write_text("hi", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("no", encoding="utf-8")
    granted = tmp_path / "granted"
    (granted / "deep").mkdir(parents=True)
    return {"root": tmp_path, "ws": ws, "outside": outside,
            "granted": granted}


# -- names and constants ---------------------------------------------------


def test_constants_and_usage():
    assert PATH_JAIL_SLICE == "M-099"
    assert SETTING_KEY == "path_jail"
    assert GRANTS_KEY == "path_grants"
    assert DECISIONS == ("allow", "deny")
    assert DEFAULT_DECISION == "deny"
    assert USAGE.startswith(
        "Usage: /pathjail, /pathjail on, /pathjail off")
    assert "symlink" in PLAIN_EXPLANATION
    assert "workspace" in PLAIN_EXPLANATION


def test_is_within_is_a_component_question():
    assert is_within("/ws", "/ws") is True
    assert is_within("/ws/a/b", "/ws") is True
    assert is_within("/ws2", "/ws") is False
    assert is_within("/ws2/a", "/ws") is False
    assert is_within("/anything", "/") is True
    assert is_within("/", "/ws") is False


# -- the basic judgements ----------------------------------------------------


def test_workspace_root_itself_allowed(layout):
    decision = check_path(str(layout["ws"]), str(layout["ws"]))
    assert decision.allowed is True
    assert decision.granted_by == "workspace"
    assert decision.resolved == os.path.realpath(layout["ws"])


def test_relative_candidate_resolved_against_workspace(layout):
    decision = check_path("notes.txt", str(layout["ws"]))
    assert decision.allowed is True
    assert decision.candidate == "notes.txt"
    assert decision.resolved == os.path.realpath(
        layout["ws"] / "notes.txt")
    deep = check_path("sub/../notes.txt", str(layout["ws"]))
    assert deep.allowed is True


def test_absolute_outside_denied(layout):
    target = str(layout["outside"] / "secret.txt")
    decision = check_path(target, str(layout["ws"]))
    assert decision.allowed is False
    assert decision.decision == "deny"
    assert decision.granted_by is None
    assert "outside the workspace" in decision.reason


def test_dotdot_escape_denied(layout):
    decision = check_path("../outside/secret.txt", str(layout["ws"]))
    assert decision.allowed is False
    assert decision.resolved == os.path.realpath(
        layout["outside"] / "secret.txt")
    absolute = check_path(
        str(layout["ws"] / "sub" / ".." / ".." / "outside"),
        str(layout["ws"]))
    assert absolute.allowed is False


def test_sibling_prefix_trick_denied(layout):
    sibling = layout["root"] / "ws2"
    sibling.mkdir()
    decision = check_path(str(sibling / "x.txt"), str(layout["ws"]))
    assert decision.allowed is False


def test_nonexistent_deep_path_under_workspace_allowed(layout):
    decision = check_path("a/b/c/new.txt", str(layout["ws"]))
    assert decision.allowed is True
    assert decision.resolved == os.path.realpath(
        layout["ws"] / "a" / "b" / "c" / "new.txt")


# -- symlinks: resolved, never assumed away ----------------------------------


def test_symlinked_dir_inside_pointing_outside_denied(layout):
    os.symlink(layout["outside"], layout["ws"] / "escape")
    decision = check_path("escape/secret.txt", str(layout["ws"]))
    assert decision.allowed is False
    assert decision.resolved == os.path.realpath(
        layout["outside"] / "secret.txt")


def test_symlink_escape_with_nonexistent_tail_denied(layout):
    os.symlink(layout["outside"], layout["ws"] / "escape")
    decision = check_path("escape/not-yet.txt", str(layout["ws"]))
    assert decision.allowed is False
    assert decision.resolved == os.path.realpath(
        layout["outside"] / "not-yet.txt")


def test_symlinked_file_inside_pointing_outside_denied(layout):
    os.symlink(layout["outside"] / "secret.txt", layout["ws"] / "link.txt")
    decision = check_path("link.txt", str(layout["ws"]))
    assert decision.allowed is False


def test_symlinked_dir_outside_pointing_in_judged_by_resolved(layout):
    os.symlink(layout["ws"] / "sub", layout["outside"] / "inlink")
    candidate = str(layout["outside"] / "inlink" / "file.txt")
    decision = check_path(candidate, str(layout["ws"]))
    assert decision.allowed is True
    assert decision.granted_by == "workspace"
    assert decision.resolved == os.path.realpath(
        layout["ws"] / "sub" / "file.txt")


def test_symlink_inside_pointing_inside_allowed(layout):
    os.symlink(layout["ws"] / "sub", layout["ws"] / "inner")
    decision = check_path("inner/file.txt", str(layout["ws"]))
    assert decision.allowed is True


def test_workspace_root_reached_through_a_symlink(layout):
    link_root = layout["root"] / "ws-link"
    os.symlink(layout["ws"], link_root)
    assert resolve_workspace_root(str(link_root)) == os.path.realpath(
        layout["ws"])
    decision = check_path("notes.txt", str(link_root))
    assert decision.allowed is True


# -- grants --------------------------------------------------------------------


def test_grant_allows_exactly_its_subtree(layout):
    grants = build_grants([str(layout["granted"])])
    ws = str(layout["ws"])
    assert check_path(str(layout["granted"]), ws, grants).allowed is True
    inner = check_path(
        str(layout["granted"] / "deep" / "f.txt"), ws, grants)
    assert inner.allowed is True
    assert inner.granted_by == os.path.realpath(layout["granted"])
    assert check_path(str(layout["root"]), ws, grants).allowed is False
    sibling = layout["root"] / "granted2"
    sibling.mkdir()
    assert check_path(str(sibling), ws, grants).allowed is False


def test_workspace_wins_when_a_grant_sits_inside_it(layout):
    grants = build_grants([str(layout["ws"] / "sub")])
    decision = check_path("sub/f.txt", str(layout["ws"]), grants)
    assert decision.allowed is True
    assert decision.granted_by == "workspace"


def test_normalize_and_validate_grant_forms(layout):
    want = os.path.realpath(layout["granted"])
    assert normalize_grant(str(layout["granted"]) + "/") == want
    messy = str(layout["root"] / "outside" / ".." / "granted")
    assert normalize_grant(messy) == want
    assert validate_grant({"path": str(layout["granted"])}) == want
    assert validate_grant(layout["granted"]) == want


def test_build_grants_dedupes_and_empty():
    assert build_grants(None) == ()
    assert build_grants([]) == ()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        assert build_grants([td, td + "/", {"path": td}]) == (
            os.path.realpath(td),)


def test_relative_grant_refuses(layout):
    with pytest.raises(ValueError):
        normalize_grant("relative/path")
    with pytest.raises(ValueError):
        build_grants(["relative/path"])
    with pytest.raises(ValueError):
        check_path("notes.txt", str(layout["ws"]), ["relative/path"])


def test_malformed_grants_raise(layout):
    for bad in ("", "   ", 123, None, {"bogus": "/tmp"},
                {"path": "/tmp", "extra": 1}, {"path": "rel"}):
        with pytest.raises(ValueError):
            validate_grant(bad)
    with pytest.raises(ValueError):
        build_grants("/tmp")
    with pytest.raises(ValueError):
        build_grants([str(layout["granted"]), "relative"])
    with pytest.raises(ValueError):
        check_path("notes.txt", str(layout["ws"]), "/tmp")


# -- malformed inputs ----------------------------------------------------------


def test_malformed_candidate_denied_not_raised(layout):
    ws = str(layout["ws"])
    for bad in ("", "   ", None, 123, b"/tmp/x", "a\x00b"):
        decision = check_path(bad, ws)
        assert decision.allowed is False
        assert decision.decision == "deny"
        assert decision.resolved is None
        assert decision.granted_by is None


def test_malformed_workspace_raises(layout):
    for bad in ("", "   ", None, 42):
        with pytest.raises(ValueError):
            check_path("notes.txt", bad)
        with pytest.raises(ValueError):
            resolve_workspace_root(bad)


def test_decide_path_is_check_path(layout):
    decision = decide_path("notes.txt", str(layout["ws"]))
    assert decision.allowed is True


# -- records and refusals -------------------------------------------------------


def test_decision_record_shape(layout):
    decision = check_path("notes.txt", str(layout["ws"]))
    record = decision.to_record()
    assert record["type"] == "path_jail_decision"
    assert record["slice"] == "M-099"
    assert record["decision"] == "allow"
    assert record["candidate"] == "notes.txt"
    assert record["granted_by"] == "workspace"
    assert record["resolved"] == decision.resolved
    assert record["workspace"] == decision.workspace


def test_refusal_record_is_news(layout):
    decision = check_path(
        str(layout["outside"] / "secret.txt"), str(layout["ws"]))
    refusal = build_refusal(decision)
    assert isinstance(refusal, JailRefusal)
    assert refusal.headline.startswith("Path jail refusal:")
    record = refusal_record(decision)
    assert record["type"] == "path_jail_refusal"
    assert record["slice"] == "M-099"
    assert record["news"] is True
    assert record["surface"] == "session_event"
    assert record["headline"] == refusal.headline
    assert format_refusal(refusal) == refusal.headline
    assert format_refusal(record) == refusal.headline
    with pytest.raises(ValueError):
        format_refusal({"type": "something_else"})


def test_allowed_decision_has_no_refusal(layout):
    decision = check_path("notes.txt", str(layout["ws"]))
    with pytest.raises(ValueError):
        build_refusal(decision)


# -- config readers and the gate --------------------------------------------------


def test_enabled_from_config(layout):
    assert enabled_from_config({}) is True
    assert enabled_from_config({SETTING_KEY: False}) is False
    assert enabled_from_config({SETTING_KEY: True}) is True
    for bad in ("yes", 1, None):
        with pytest.raises(ValueError):
            enabled_from_config({SETTING_KEY: bad})


def test_grants_and_jail_from_config(layout):
    assert grants_from_config({}) == ()
    config = {GRANTS_KEY: [str(layout["granted"]) ]}
    want = (os.path.realpath(layout["granted"]),)
    assert grants_from_config(config) == want
    jail = jail_from_config(config)
    assert jail.grants == want
    decision = jail.check(
        str(layout["granted"] / "f.txt"), str(layout["ws"]))
    assert decision.allowed is True
    assert jail.to_record() == {
        "type": "path_jail", "slice": "M-099", "default": "deny",
        "grants": list(want)}
    with pytest.raises(ValueError):
        grants_from_config({GRANTS_KEY: ["relative"]})


def test_pathjail_dataclass_check_defaults(layout):
    jail = PathJail()
    assert jail.check("notes.txt", str(layout["ws"])).allowed is True
    assert jail.check("/etc/passwd", str(layout["ws"])).allowed is False


def test_set_enabled_and_gate_change(layout):
    enabled, change = set_enabled({}, False)
    assert enabled is False
    assert change.event() == {
        "type": "path_jail_setting_changed", "from": True, "to": False}
    record = change.record("sess-1", True)
    assert record["type"] == "path_jail_setting_changed"
    assert record["session_id"] == "sess-1"
    assert record["journaled"] is True
    assert format_gate_change(record) == "The path jail is now off."
    assert format_gate_change(change.event()) == "The path jail is now off."
    with pytest.raises(ValueError):
        set_enabled({}, True)
    with pytest.raises(ValueError):
        set_enabled({SETTING_KEY: False}, False)
    with pytest.raises(ValueError):
        set_enabled({}, "off")


# -- the /pathjail surface ----------------------------------------------------------


def test_parse_pathjail_args_actions(layout):
    assert parse_pathjail_args("") == {"action": "show"}
    assert parse_pathjail_args("show") == {"action": "show"}
    assert parse_pathjail_args("on") == {"action": "on"}
    assert parse_pathjail_args("off") == {"action": "off"}
    assert parse_pathjail_args("grants") == {"action": "grants"}
    assert parse_pathjail_args("check notes.txt") == {
        "action": "check", "path": "notes.txt"}
    spaced = parse_pathjail_args("check my file.txt")
    assert spaced == {"action": "check", "path": "my file.txt"}
    granted = parse_pathjail_args(f"grant {layout['granted']}")
    assert granted == {
        "action": "grant",
        "grant": os.path.realpath(layout["granted"])}


def test_parse_pathjail_args_errors():
    for bad in ("frobnicate", "check", "grant", "on please"):
        with pytest.raises(ValueError) as excinfo:
            parse_pathjail_args(bad)
        assert str(excinfo.value) == USAGE
    with pytest.raises(ValueError):
        parse_pathjail_args("grant relative/path")


def test_format_grants(layout):
    assert format_grants(()) == (
        "Path grants: none - only the workspace itself is allowed.")
    text = format_grants((os.path.realpath(layout["granted"]),))
    assert text.startswith("Path grants:")
    assert os.path.realpath(layout["granted"]) in text


def test_format_jail_decision(layout):
    allowed = check_path("notes.txt", str(layout["ws"]))
    assert format_jail_decision(allowed).startswith("Path allowed:")
    denied = check_path("/etc/passwd", str(layout["ws"]))
    assert format_jail_decision(denied).startswith("Path jail refusal:")


def test_format_path_jail_whole_slice(layout):
    config = {GRANTS_KEY: [str(layout["granted"])]}
    text = format_path_jail(config, str(layout["ws"]))
    assert "M-099" in text
    assert PLAIN_EXPLANATION in text
    assert "Setting: on (path_jail)." in text
    assert os.path.realpath(layout["ws"]) in text
    assert "Default posture: deny (fail-closed)." in text
    assert os.path.realpath(layout["granted"]) in text
    assert "Sample check (notes.txt inside the workspace): " in text
    assert "Path allowed:" in text
    assert text.endswith(USAGE)
    off = format_path_jail({SETTING_KEY: False}, str(layout["ws"]))
    assert "Setting: off (path_jail)." in off


# -- agent layer: status, set, grants, check, surfaces (M-099) -------

import copy as _copy

from mythic_agent.core import path_jail as pj
from mythic_agent.core.sessions import SessionStore


class _OfflineMemory:
    def __init__(self):
        self.archived = []

    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        self.archived.append(text)


@pytest.fixture()
def agent(tmp_path, monkeypatch):
    from mythic_agent.agents import llm
    from mythic_agent.core.secure_api import unsubscribe

    config = {"model": "test-model", "base_url": "http://localhost:1/v1", "api_keys": {}}
    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(llm.config_manager, "load_config", lambda: _copy.deepcopy(config))
    monkeypatch.setattr(llm.config_manager, "save_config", lambda config: True)
    monkeypatch.setattr(llm, "get_vector_provider", lambda *args: _OfflineMemory())
    instance = llm.Agent(project_root=tmp_path)
    from mythic_agent.core.policy import ToolPolicy
    instance.tool_policy = ToolPolicy("trusted")
    yield instance
    unsubscribe("agent_clear_history", instance._handle_clear_history)
    unsubscribe("agent_compact_history", instance._handle_compact_history)


def _store_for(tmp_path):
    return SessionStore(tmp_path, tmp_path / "state")


def _events(store, session_id, type_name):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == type_name]


def _outside(tmp_path):
    path = tmp_path.parent / (tmp_path.name + "-outside")
    path.mkdir(exist_ok=True)
    return path


class TestPathJailAgent:
    def test_status_defaults_on(self, agent):
        status = agent.path_jail_status()
        assert status["enabled"] is True
        assert status["grants"] == []
        assert status["workspace"] == os.path.realpath(agent.project_root)
        assert status["screen"] == format_path_jail(
            agent.config, str(agent.project_root))
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_status_reflects_off(self, agent):
        agent.config[SETTING_KEY] = False
        assert agent.path_jail_status()["enabled"] is False

    def test_status_reflects_grants(self, agent, tmp_path):
        granted = _outside(tmp_path) / "granted"
        granted.mkdir(exist_ok=True)
        agent.add_path_grant(str(granted))
        status = agent.path_jail_status()
        assert status["grants"] == [os.path.realpath(granted)]

    def test_status_malformed_config_raises(self, agent):
        agent.config[SETTING_KEY] = "yes"
        with pytest.raises(ValueError):
            agent.path_jail_status()
        agent.config[SETTING_KEY] = True
        agent.config[GRANTS_KEY] = ["relative/path"]
        with pytest.raises(ValueError):
            agent.path_jail_status()

    def test_set_off_then_on(self, agent):
        record = agent.set_path_jail(False)
        assert record["type"] == "path_jail_setting_changed"
        assert record["from"] is True and record["to"] is False
        assert record["journaled"] is False
        assert agent.config[SETTING_KEY] is False
        assert format_gate_change(record) == "The path jail is now off."
        record = agent.set_path_jail(True)
        assert record["from"] is False and record["to"] is True
        assert format_gate_change(record) == "The path jail is now on."

    def test_set_noop_refuses_and_changes_nothing(self, agent):
        with pytest.raises(ValueError, match="already on"):
            agent.set_path_jail(True)
        assert SETTING_KEY not in agent.config
        with pytest.raises(ValueError):
            agent.set_path_jail("off")

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.set_path_jail(False)
        assert record["journaled"] is True
        events = _events(store, session_id, "path_jail_setting_changed")
        assert len(events) == 1
        assert events[0]["from"] is True and events[0]["to"] is False
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_path_jail(False)
        assert SETTING_KEY not in agent.config
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["path_jail_setting_changed",
                              "path_jail_setting_reverted"]
        agent.close()

    def test_add_grant_stores_plain_string_and_refuses(self, agent, tmp_path):
        granted = _outside(tmp_path) / "granted"
        granted.mkdir(exist_ok=True)
        want = os.path.realpath(granted)
        record = agent.add_path_grant(str(granted))
        assert record["type"] == "path_grants_changed"
        assert record["grant"] == want
        assert record["journaled"] is False
        assert agent.config[GRANTS_KEY] == [want]
        with pytest.raises(ValueError, match="already"):
            agent.add_path_grant(str(granted))
        with pytest.raises(ValueError):
            agent.add_path_grant("relative/path")
        with pytest.raises(ValueError):
            agent.add_path_grant({"path": str(granted), "extra": 1})
        assert agent.config[GRANTS_KEY] == [want]

    def test_add_journals_on_the_session(self, agent, tmp_path):
        granted = _outside(tmp_path) / "granted"
        granted.mkdir(exist_ok=True)
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.add_path_grant(str(granted))
        assert record["journaled"] is True
        events = _events(store, session_id, "path_grants_changed")
        assert len(events) == 1
        assert events[0]["action"] == "grant"
        assert events[0]["grant"] == os.path.realpath(granted)
        agent.close()

    def test_add_save_failure_restores_previous_grants(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        first = _outside(tmp_path) / "first"
        first.mkdir(exist_ok=True)
        second = _outside(tmp_path) / "second"
        second.mkdir(exist_ok=True)
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.add_path_grant(str(first))
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.add_path_grant(str(second))
        assert agent.config[GRANTS_KEY] == [os.path.realpath(first)]
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["path_grants_changed",
                              "path_grants_reverted"]
        agent.close()


class TestCheckPathJail:
    def test_allowed_path_publishes_nothing(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        before = len(store.export(session_id)["events"])
        decision = agent.check_path_jail("notes.txt")
        assert decision.allowed is True
        assert decision.decision == "allow"
        assert decision.granted_by == "workspace"
        assert len(store.export(session_id)["events"]) == before
        assert _events(store, session_id, "path_jail_refusal") == []
        agent.close()

    def test_denied_path_publishes_refusal_news(self, agent, tmp_path):
        outside = _outside(tmp_path)
        target = str(outside / "secret.txt")
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        decision = agent.check_path_jail(target)
        assert decision.allowed is False
        events = _events(store, session_id, "path_jail_refusal")
        assert len(events) == 1
        assert events[0]["news"] is True
        assert events[0]["surface"] == "session_event"
        assert events[0]["candidate"] == target
        assert events[0]["resolved"] == os.path.realpath(target)
        agent.close()

    def test_denied_path_with_gate_off_publishes_nothing(
            self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.config[SETTING_KEY] = False
        decision = agent.check_path_jail(
            str(_outside(tmp_path) / "secret.txt"))
        assert decision.allowed is False
        assert _events(store, session_id, "path_jail_refusal") == []
        agent.close()

    def test_granted_outside_path_is_allowed(self, agent, tmp_path):
        granted = _outside(tmp_path) / "granted"
        (granted / "deep").mkdir(parents=True, exist_ok=True)
        agent.add_path_grant(str(granted))
        decision = agent.check_path_jail(str(granted / "deep" / "f.txt"))
        assert decision.allowed is True
        assert decision.granted_by == os.path.realpath(granted)

    def test_symlink_escape_is_denied_and_published(self, agent, tmp_path):
        outside = _outside(tmp_path)
        (outside / "secret.txt").write_text("no", encoding="utf-8")
        os.symlink(outside, tmp_path / "escape")
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        decision = agent.check_path_jail("escape/secret.txt")
        assert decision.allowed is False
        assert decision.resolved == os.path.realpath(
            outside / "secret.txt")
        assert len(_events(store, session_id, "path_jail_refusal")) == 1
        agent.close()

    def test_malformed_candidate_is_denied_not_raised(self, agent):
        decision = agent.check_path_jail("")
        assert decision.allowed is False
        assert decision.decision == "deny"


class TestPathJailTerminalSurface:
    def test_show_is_the_whole_slice(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/pathjail")
        assert "M-099" in text and "Setting: on (path_jail)" in text

    def test_grants_empty_message(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/pathjail grants")
        assert "Path grants: none" in text

    def test_check_denied_headline(self, agent, tmp_path):
        from mythic_agent.terminal import _slash
        target = str(_outside(tmp_path) / "secret.txt")
        _, _, text = _slash(agent, f"/pathjail check {target}")
        assert text.startswith("Path jail refusal:")

    def test_check_allowed_inside_workspace(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/pathjail check notes.txt")
        assert text.startswith("Path allowed:")

    def test_grant_then_check_allowed(self, agent, tmp_path):
        from mythic_agent.terminal import _slash
        granted = _outside(tmp_path) / "granted"
        granted.mkdir(exist_ok=True)
        _, _, text = _slash(agent, f"/pathjail grant {granted}")
        assert os.path.realpath(granted) in text
        _, _, text = _slash(agent, "/pathjail grants")
        assert os.path.realpath(granted) in text
        _, _, text = _slash(
            agent, f"/pathjail check {granted}/deep/f.txt")
        assert text.startswith("Path allowed:")

    def test_gate_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/pathjail off")
        assert text == "The path jail is now off."
        assert agent.config[SETTING_KEY] is False
        _, _, text = _slash(agent, "/pathjail off")
        assert "already off" in text
        _, _, text = _slash(agent, "/pathjail on")
        assert text == "The path jail is now on."

    def test_bad_grammar_is_the_usage(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/pathjail frobnicate")
        assert text.startswith("Usage: /pathjail")
        assert text == USAGE


@pytest.fixture()
def pathjail_handler(agent, monkeypatch):
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


def _pathjail_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPathJailCommand:
    def test_show_is_default(self, pathjail_handler, agent):
        pathjail_handler._handle_pathjail("")
        text = _pathjail_published_text(pathjail_handler)
        assert "M-099" in text and "Setting: on" in text

    def test_check_denied_is_published(self, pathjail_handler, agent, tmp_path):
        target = str(_outside(tmp_path) / "secret.txt")
        pathjail_handler._handle_pathjail(f"check {target}")
        assert "Path jail refusal:" in _pathjail_published_text(pathjail_handler)

    def test_grant_is_published_and_stored(self, pathjail_handler, agent, tmp_path):
        granted = _outside(tmp_path) / "granted"
        granted.mkdir(exist_ok=True)
        pathjail_handler._handle_pathjail(f"grant {granted}")
        assert os.path.realpath(granted) in _pathjail_published_text(pathjail_handler)
        assert agent.config[GRANTS_KEY] == [os.path.realpath(granted)]

    def test_gate_via_the_handler(self, pathjail_handler, agent):
        pathjail_handler._handle_pathjail("off")
        assert "now off" in _pathjail_published_text(pathjail_handler)
        assert agent.config[SETTING_KEY] is False

    def test_bad_grammar_is_published(self, pathjail_handler, agent):
        pathjail_handler._handle_pathjail("frobnicate")
        assert "Usage: /pathjail" in _pathjail_published_text(pathjail_handler)


class TestChatScreenRouting:
    def test_pathjail_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/pathjail off", _FakeLog())
        assert calls == [("/pathjail", "off")]
