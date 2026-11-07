"""M-102 Hook packs - pure-layer tests.

TIER: integration

The pure layer is the house hooks shipped as
installable packs: each pack a named, described set
of M-101 hooks validated through the hooks layer,
a shipped catalogue with lookup by name, and install
as pure data - explicit, idempotent, never mutating
its input. Malformed data raises, one bad entry
refuses the whole, and the README guard never
modifies a README.
"""

import pytest

from mythic_agent.core.hook_packs import (
    HOOK_PACKS_SLICE,
    PACK_NAMES,
    PLAIN_EXPLANATION,
    SHIPPED_PACKS,
    USAGE,
    Pack,
    build_pack,
    build_packs,
    format_hook_packs,
    format_pack,
    format_packs,
    format_packs_status,
    get_pack,
    hooks_for_pack,
    install_pack,
    normalize_pack_name,
    pack_label,
    parse_hook_packs_args,
    resolve_pack,
    shipped_packs,
    validate_pack,
    validate_packs,
)
from mythic_agent.core.hooks import HOOK_EVENTS, Hook, validate_hooks


def _pack_spec(**overrides):
    spec = {
        "name": "my_pack",
        "description": "A pack of my own.",
        "hooks": [{"event": "post_edit", "command": "pytest -q",
                   "name": "mine"}],
    }
    spec.update(overrides)
    return spec


# -- names and constants ---------------------------------------------------


def test_constants_and_usage():
    assert HOOK_PACKS_SLICE == "M-102"
    assert PACK_NAMES == (
        "tests_after_edits", "readme_guard", "verify_pushes")
    assert USAGE.startswith("Usage: /hookpacks")
    assert "install" in USAGE
    assert "tests_after_edits" in PLAIN_EXPLANATION
    assert "readme_guard" in PLAIN_EXPLANATION
    assert "verify_pushes" in PLAIN_EXPLANATION


def test_normalize_pack_name_case_and_dashes():
    assert normalize_pack_name("readme_guard") == "readme_guard"
    assert normalize_pack_name("README-GUARD") == "readme_guard"
    assert normalize_pack_name(" Tests-After-Edits ") == "tests_after_edits"
    assert pack_label(get_pack("verify_pushes")) == "verify_pushes"


def test_normalize_pack_name_bad_raises():
    for bad in ("", "   ", "has space", "no/slash", None, 7):
        with pytest.raises(ValueError):
            normalize_pack_name(bad)


# -- the shipped catalogue ---------------------------------------------------


def test_catalogue_is_three_shipped_packs_in_order():
    assert shipped_packs() == SHIPPED_PACKS
    assert [p.name for p in SHIPPED_PACKS] == list(PACK_NAMES)
    for pack in SHIPPED_PACKS:
        assert isinstance(pack, Pack)
        assert pack.description
        assert pack.hook_count >= 1
        assert pack.to_record()["name"] == pack.name


def test_tests_after_edits_pack_runs_tests_after_edits():
    pack = get_pack("tests_after_edits")
    assert pack.events == ("post_edit",)
    commands = [h.command for h in pack.hooks]
    assert "python -m pytest -q" in commands
    for hook in pack.hooks:
        assert hook.event in HOOK_EVENTS and hook.enabled is True


def test_readme_guard_pack_is_read_only():
    pack = get_pack("readme_guard")
    assert set(pack.events) == {"on_commit", "pre_edit"}
    for hook in pack.hooks:
        assert "README" in hook.command
        assert "git diff" in hook.command
        # The guard only reads: no write-shaped command rides it.
        for word in ("checkout", "restore", "clean", "reset", ">", "rm "):
            assert word not in hook.command


def test_verify_pushes_pack_verifies_at_commit():
    pack = get_pack("verify_pushes")
    assert pack.events == ("on_commit",)
    commands = [h.command for h in pack.hooks]
    assert "python -m pytest -q" in commands
    assert "git diff --check" in commands


def test_all_shipped_hooks_are_valid_m101_hooks():
    for pack in SHIPPED_PACKS:
        hooks = hooks_for_pack(pack.name)
        assert hooks == pack.hooks
        assert validate_hooks([h.to_record() for h in hooks]) == hooks


# -- lookup --------------------------------------------------------------------


def test_get_pack_case_and_dash_insensitive():
    assert get_pack("README-GUARD") is get_pack("readme_guard")
    assert get_pack(" Verify-Pushes ").name == "verify_pushes"
    assert resolve_pack("tests-after-edits").name == "tests_after_edits"
    assert resolve_pack(get_pack("readme_guard")) is get_pack("readme_guard")


def test_get_pack_unknown_raises():
    for bad in ("nope", "", "tests", None):
        with pytest.raises(ValueError):
            get_pack(bad)
    with pytest.raises(ValueError):
        hooks_for_pack("nope")


# -- the Pack dataclass and mapping validation ----------------------------------


def test_pack_defaults_record_and_events():
    pack = validate_pack(_pack_spec())
    assert pack.name == "my_pack"
    assert pack.label == "my_pack"
    assert pack.hook_count == 1
    assert pack.events == ("post_edit",)
    record = pack.to_record()
    assert record["description"] == "A pack of my own."
    assert record["hooks"][0]["command"] == "pytest -q"
    assert validate_pack(pack) is pack
    built = build_pack("My-Pack", "Built.", [
        {"event": "on_test", "command": "pytest -q"}])
    assert built.name == "my_pack" and built.events == ("on_test",)


def test_pack_aliases_and_conflicting_spellings():
    pack = validate_pack({
        "title": "alias_pack", "summary": "Aliased.",
        "hooks": [{"event": "on_test", "command": "pytest -q"}]})
    assert pack.name == "alias_pack" and pack.description == "Aliased."
    same = validate_pack({
        "name": "x_pack", "title": "x_pack",
        "description": "D.", "summary": "D.",
        "hooks": [{"event": "on_test", "command": "pytest -q"}]})
    assert same.name == "x_pack"
    base = _pack_spec()
    with pytest.raises(ValueError):
        validate_pack({**base, "title": "other_pack"})
    with pytest.raises(ValueError):
        validate_pack({**base, "summary": "Different."})


def test_pack_unknown_and_missing_keys_raise():
    with pytest.raises(ValueError):
        validate_pack({**_pack_spec(), "telemetry": "off"})
    with pytest.raises(ValueError):
        validate_pack({"description": "D.", "hooks": []})
    with pytest.raises(ValueError):
        validate_pack({"name": "x", "hooks": []})
    with pytest.raises(ValueError):
        validate_pack({"name": "x", "description": "D."})
    with pytest.raises(ValueError):
        validate_pack("not a mapping")


def test_pack_empty_name_description_and_hooks_raise():
    with pytest.raises(ValueError):
        validate_pack(_pack_spec(name="  "))
    with pytest.raises(ValueError):
        validate_pack(_pack_spec(description=""))
    with pytest.raises(ValueError):
        validate_pack(_pack_spec(hooks=[]))
    with pytest.raises(ValueError):
        Pack(name="x", description="D.", hooks=())
    with pytest.raises(ValueError):
        Pack(name="x", description="D.", hooks=("not a hook",))


def test_pack_bad_hook_refuses_whole_pack():
    with pytest.raises(ValueError):
        validate_pack(_pack_spec(hooks=[
            {"event": "post_edit", "command": "pytest -q"},
            {"event": "whenever", "command": "x.sh"}]))
    with pytest.raises(ValueError):
        validate_pack(_pack_spec(hooks=[
            {"event": "post_edit", "command": "   "}]))
    with pytest.raises(ValueError):
        validate_pack(_pack_spec(hooks=[
            {"event": "post_edit", "command": "x.sh", "bogus": 1}]))


def test_pack_duplicate_hook_names_and_pairs_raise():
    with pytest.raises(ValueError):
        validate_pack(_pack_spec(hooks=[
            {"event": "post_edit", "command": "a.sh", "name": "Same"},
            {"event": "on_test", "command": "b.sh", "name": "same"}]))
    with pytest.raises(ValueError):
        validate_pack(_pack_spec(hooks=[
            {"event": "post_edit", "command": "a.sh"},
            {"event": "post_edit", "command": "a.sh"}]))


def test_validate_packs_list_rules_and_duplicate_names():
    assert validate_packs(None) == ()
    assert build_packs(None) == ()
    assert validate_packs([]) == ()
    packs = validate_packs([_pack_spec(), _pack_spec(name="other")])
    assert [p.name for p in packs] == ["my_pack", "other"]
    with pytest.raises(ValueError):
        validate_packs([_pack_spec(), _pack_spec(name="MY-PACK")])
    with pytest.raises(ValueError):
        validate_packs([_pack_spec(), _pack_spec(hooks=[])])
    with pytest.raises(ValueError):
        validate_packs("my_pack")


# -- install, as pure data --------------------------------------------------------


def test_install_into_empty_and_none():
    installed = install_pack([], "readme_guard")
    assert installed == get_pack("readme_guard").hooks
    assert install_pack(None, "readme_guard") == installed
    assert isinstance(installed, tuple)


def test_install_appends_after_existing_in_pack_order():
    existing = validate_hooks([
        {"event": "on_session", "command": "hello.sh", "name": "hello"}])
    installed = install_pack(existing, "verify_pushes")
    assert installed[:1] == existing
    assert installed[1:] == get_pack("verify_pushes").hooks


def test_install_is_idempotent():
    once = install_pack([], "tests_after_edits")
    twice = install_pack(once, "tests_after_edits")
    assert twice == once
    both = install_pack(once, "verify_pushes")
    assert install_pack(both, "tests_after_edits") == both
    assert install_pack(both, "verify_pushes") == both


def test_install_skips_hooks_already_present_by_event_and_command():
    existing = validate_hooks([
        {"event": "post_edit", "command": "python -m pytest -q",
         "name": "my-own-name"}])
    installed = install_pack(existing, "tests_after_edits")
    commands = [h.command for h in installed]
    assert commands.count("python -m pytest -q") == 1
    assert "python -m compileall -q mythic_agent" in commands
    assert len(installed) == 2


def test_install_name_collision_with_different_hook_refuses():
    existing = validate_hooks([
        {"event": "on_session", "command": "other.sh",
         "name": "run-tests-after-edit"}])
    with pytest.raises(ValueError):
        install_pack(existing, "tests_after_edits")


def test_install_never_mutates_input():
    existing = [{"event": "on_session", "command": "hello.sh"}]
    snapshot = [dict(existing[0])]
    installed = install_pack(existing, "verify_pushes")
    assert existing == snapshot
    assert len(installed) == 3
    as_hooks = list(validate_hooks([
        {"event": "on_session", "command": "hello.sh"}]))
    before = list(as_hooks)
    install_pack(as_hooks, "verify_pushes")
    assert as_hooks == before


def test_install_malformed_existing_and_unknown_pack_raise():
    with pytest.raises(ValueError):
        install_pack([{"event": "pre_tool"}], "readme_guard")
    with pytest.raises(ValueError):
        install_pack([], "nope")
    with pytest.raises(ValueError):
        install_pack("pytest -q", "readme_guard")
    by_object = install_pack([], get_pack("verify_pushes"))
    by_mapping = install_pack([], _pack_spec())
    assert by_object == get_pack("verify_pushes").hooks
    assert by_mapping[0].command == "pytest -q"


# -- the /hookpacks surface --------------------------------------------------------


def test_format_pack_one_line():
    text = format_pack("readme_guard")
    assert text.startswith("readme_guard: ")
    assert "2 hook(s)" in text and "on_commit" in text
    assert format_pack(get_pack("verify_pushes")).startswith("verify_pushes: ")
    with pytest.raises(ValueError):
        format_pack("nope")


def test_format_packs_lists_shelf_in_order():
    text = format_packs()
    assert text.startswith("Hook packs: 3 shipped.")
    assert text.index("tests_after_edits") < text.index("readme_guard")
    assert text.index("readme_guard") < text.index("verify_pushes")
    assert format_packs([]).startswith("Hook packs: none shipped.")
    assert format_packs(None) == text


def test_format_packs_status_one_line():
    text = format_packs_status()
    assert text.startswith("Hook packs: 3 shipped (")
    assert "tests_after_edits" in text and "6 hook(s)" in text
    assert format_packs_status([]) == "Hook packs: none shipped."


def test_format_hook_packs_whole_surface():
    text = format_hook_packs()
    assert text.startswith("Hook packs (M-102) - ")
    assert "Hook packs: 3 shipped." in text
    assert text.rstrip().endswith(USAGE.rstrip().split(", ")[-1]) or USAGE in text
    assert USAGE in text


def test_parse_hook_packs_args_show_forms():
    assert parse_hook_packs_args("") == ("show", None)
    assert parse_hook_packs_args(None) == ("show", None)
    assert parse_hook_packs_args("list") == ("show", None)
    assert parse_hook_packs_args("show") == ("show", None)
    assert parse_hook_packs_args("show readme_guard") == (
        "show", "readme_guard")
    assert parse_hook_packs_args("show README-GUARD") == (
        "show", "readme_guard")
    assert parse_hook_packs_args("verify_pushes") == (
        "show", "verify_pushes")


def test_parse_hook_packs_args_install_and_errors():
    assert parse_hook_packs_args("install tests-after-edits") == (
        "install", "tests_after_edits")
    assert parse_hook_packs_args("install readme_guard") == (
        "install", "readme_guard")
    for bad in ("frobnicate", "install", "install nope", "show a b",
                "install readme_guard extra", "remove readme_guard", 7):
        with pytest.raises(ValueError) as excinfo:
            parse_hook_packs_args(bad)
        assert str(excinfo.value) == USAGE

# -- agent layer: status, install, surfaces (M-102) ---

import copy as _copy

from mythic_agent.core.hooks import SETTING_KEY as HOOKS_SETTING_KEY
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


def _configure_hooks(agent, *specs):
    agent.config[HOOKS_SETTING_KEY] = list(specs)


class TestHookPacksAgentStatus:
    def test_status_defaults_to_nothing_installed(self, agent):
        status = agent.hook_packs_status()
        assert [p["name"] for p in status["packs"]] == list(PACK_NAMES)
        assert status["installed"] == {
            "tests_after_edits": False,
            "readme_guard": False,
            "verify_pushes": False}
        assert status["hooks"] == []
        assert status["screen"] == format_hook_packs()
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_status_reflects_configured_hooks(self, agent):
        _configure_hooks(agent, *[
            h.to_record() for h in get_pack("readme_guard").hooks])
        status = agent.hook_packs_status()
        assert status["installed"]["readme_guard"] is True
        assert status["installed"]["verify_pushes"] is False
        assert len(status["hooks"]) == 2

    def test_status_partial_install_is_not_installed(self, agent):
        first = get_pack("verify_pushes").hooks[0]
        _configure_hooks(agent, first.to_record())
        status = agent.hook_packs_status()
        assert status["installed"]["verify_pushes"] is False

    def test_status_malformed_config_raises(self, agent):
        _configure_hooks(agent, {"event": "pre_tool"})
        with pytest.raises(ValueError):
            agent.hook_packs_status()
        agent.config[HOOKS_SETTING_KEY] = "pytest -q"
        with pytest.raises(ValueError):
            agent.hook_packs_status()


class TestInstallHookPack:
    def test_install_happy_path_stores_plain_records(self, agent):
        record = agent.install_hook_pack("readme_guard")
        assert record["type"] == "hook_pack_installed"
        assert record["pack"] == "readme_guard"
        assert record["changed"] is True
        assert record["journaled"] is False
        assert len(record["added"]) == 2
        stored = agent.config[HOOKS_SETTING_KEY]
        assert stored == [
            h.to_record() for h in get_pack("readme_guard").hooks]
        assert agent.hook_packs_status()["installed"]["readme_guard"] is True
        assert [h.command for h in agent.configured_hooks()] == [
            h.command for h in get_pack("readme_guard").hooks]

    def test_install_reads_the_name_case_and_dash_insensitively(self, agent):
        record = agent.install_hook_pack("README-GUARD")
        assert record["pack"] == "readme_guard" and record["changed"] is True

    def test_install_accepts_a_pack_object(self, agent):
        record = agent.install_hook_pack(get_pack("verify_pushes"))
        assert record["pack"] == "verify_pushes"
        assert len(agent.config[HOOKS_SETTING_KEY]) == 2

    def test_install_appends_after_existing_in_pack_order(self, agent):
        _configure_hooks(agent,
                         {"event": "on_session", "command": "hello.sh",
                          "name": "hello"})
        record = agent.install_hook_pack("verify_pushes")
        stored = agent.config[HOOKS_SETTING_KEY]
        assert stored[0]["command"] == "hello.sh"
        assert stored[1:] == [
            h.to_record() for h in get_pack("verify_pushes").hooks]
        assert len(record["added"]) == 2

    def test_install_partial_adds_only_the_missing_hooks(self, agent):
        first = get_pack("tests_after_edits").hooks[0]
        _configure_hooks(agent, {"event": first.event,
                                 "command": first.command,
                                 "name": "my-own-name"})
        record = agent.install_hook_pack("tests_after_edits")
        assert record["changed"] is True
        assert len(record["added"]) == 1
        assert record["added"][0]["command"] == (
            "python -m compileall -q mythic_agent")
        assert len(agent.config[HOOKS_SETTING_KEY]) == 2

    def test_install_idempotent_writes_and_journals_nothing(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        first = agent.install_hook_pack("tests_after_edits")
        assert first["changed"] is True and first["journaled"] is True
        before = _copy.deepcopy(agent.config)
        saves = []
        monkeypatch.setattr(
            llm.config_manager, "save_config",
            lambda config: saves.append(config) or False)
        second = agent.install_hook_pack("tests_after_edits")
        assert second["changed"] is False
        assert second["journaled"] is False
        assert second["added"] == []
        assert saves == []
        assert agent.config == before
        events = _events(store, session_id, "hook_pack_installed")
        assert len(events) == 1
        agent.close()

    def test_install_journals_on_the_session(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.install_hook_pack("verify_pushes")
        assert record["journaled"] is True
        events = _events(store, session_id, "hook_pack_installed")
        assert len(events) == 1
        assert events[0]["pack"] == "verify_pushes"
        assert len(events[0]["added"]) == 2
        agent.close()

    def test_install_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        _configure_hooks(agent,
                         {"event": "on_session", "command": "hello.sh"})
        before = _copy.deepcopy(agent.config)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.install_hook_pack("readme_guard")
        assert agent.config == before
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["hook_pack_installed",
                              "hook_pack_install_reverted"]
        agent.close()

    def test_install_unknown_pack_raises_and_writes_nothing(self, agent):
        with pytest.raises(ValueError):
            agent.install_hook_pack("nope")
        assert HOOKS_SETTING_KEY not in agent.config

    def test_install_name_collision_refuses_and_writes_nothing(self, agent):
        _configure_hooks(agent,
                         {"event": "on_session", "command": "other.sh",
                          "name": "run-tests-after-edit"})
        before = _copy.deepcopy(agent.config)
        with pytest.raises(ValueError):
            agent.install_hook_pack("tests_after_edits")
        assert agent.config == before

    def test_install_malformed_existing_hooks_raise(self, agent):
        _configure_hooks(agent, {"event": "pre_tool"})
        with pytest.raises(ValueError):
            agent.install_hook_pack("readme_guard")


class TestHookPacksTerminalSurface:
    def test_show_is_the_whole_slice(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hookpacks")
        assert text.startswith("Hook packs (M-102) - ")
        assert "Hook packs: 3 shipped." in text

    def test_show_one_pack_gives_its_details(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hookpacks show readme_guard")
        assert text.startswith("readme_guard: ")
        assert "git diff --quiet -- README.md" in text
        _, _, text = _slash(agent, "/hookpacks verify-pushes")
        assert text.startswith("verify_pushes: ")

    def test_install_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hookpacks install tests-after-edits")
        assert text == (
            "Hook pack installed: tests_after_edits (2 hook(s) added).")
        assert agent.hook_packs_status()["installed"]["tests_after_edits"] is True
        _, _, text = _slash(agent, "/hookpacks install tests_after_edits")
        assert text == (
            "Hook pack tests_after_edits is already installed; "
            "nothing changed.")

    def test_bad_grammar_is_the_usage(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hookpacks frobnicate")
        assert text == USAGE
        _, _, text = _slash(agent, "/hookpacks install nope")
        assert text == USAGE


@pytest.fixture()
def hookpacks_handler(agent, monkeypatch):
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


def _hookpacks_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestHookPacksCommand:
    def test_show_is_default(self, hookpacks_handler, agent):
        hookpacks_handler._handle_hookpacks("")
        assert "Hook packs: 3 shipped." in _hookpacks_published_text(
            hookpacks_handler)

    def test_show_one_pack_is_published(self, hookpacks_handler, agent):
        hookpacks_handler._handle_hookpacks("show readme_guard")
        text = _hookpacks_published_text(hookpacks_handler)
        assert "readme_guard: " in text
        assert "git diff --cached --quiet -- README.md" in text

    def test_install_is_published(self, hookpacks_handler, agent):
        hookpacks_handler._handle_hookpacks("install verify_pushes")
        text = _hookpacks_published_text(hookpacks_handler)
        assert "Hook pack installed: verify_pushes" in text
        assert agent.hook_packs_status()["installed"]["verify_pushes"] is True
        hookpacks_handler._handle_hookpacks("install verify_pushes")
        assert "already installed" in _hookpacks_published_text(
            hookpacks_handler)

    def test_bad_grammar_is_published(self, hookpacks_handler, agent):
        hookpacks_handler._handle_hookpacks("frobnicate")
        assert "Usage: /hookpacks" in _hookpacks_published_text(
            hookpacks_handler)


class TestChatScreenRoutingHookPacks:
    def test_hookpacks_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/hookpacks install readme_guard", _FakeLog())
        assert calls == [("/hookpacks", "install readme_guard")]
