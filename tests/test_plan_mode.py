"""M-100 Plan mode perfected - pure-layer tests.

TIER: integration

The pure layer is a plan posture (read everything,
write nothing), a plan document in Part IX form
(an ordered list of slices, each with a title, an
intent, and acceptance checks), and approval of
that one plan as the single gate to building.
The gate ships OFF, decisions are mechanical,
malformed stored data raises, approval belongs
to one plan alone, and a refusal is news.
"""

import pytest

from mythic_agent.core.plan_mode import (
    DECISIONS,
    EFFECTS,
    PLAIN_EXPLANATION,
    PLAN_MODE_SLICE,
    SETTING_KEY,
    USAGE,
    Plan,
    PlanRefusal,
    PlanSlice,
    approve,
    build_plan,
    build_refusal,
    can_build,
    decide,
    enabled_from_config,
    format_gate_change,
    format_plan,
    format_plan_mode,
    format_plan_status,
    format_refusal,
    parse_plan_args,
    plan_mode_enabled,
    refusal_for_build,
    refusal_for_effect,
    refusal_record,
    set_enabled,
    validate_plan,
    validate_plan_slice,
)


def _slice(title="First slice", intent="Do the first thing",
           checks=("the first thing works",)):
    return {"title": title, "intent": intent,
            "acceptance_checks": list(checks)}


def _plan(**overrides):
    spec = {
        "title": "Ship the thing",
        "intent": "Build the thing in slices",
        "slices": [
            _slice(),
            _slice("Second slice", "Do the second thing",
                   ("the second thing works",
                    "the second thing is tested")),
        ],
    }
    spec.update(overrides)
    return validate_plan(spec)


# -- names and constants ---------------------------------------------------


def test_constants_and_usage():
    assert PLAN_MODE_SLICE == "M-100"
    assert SETTING_KEY == "plan_mode"
    assert DECISIONS == ("allow", "deny")
    assert EFFECTS == ("read", "write", "execute")
    assert USAGE.startswith("Usage: /plan, /plan show, /plan on")
    assert "acceptance checks" in PLAIN_EXPLANATION
    assert "write-nothing" in PLAIN_EXPLANATION


# -- the gate reader ---------------------------------------------------------


def test_gate_ships_off_by_default():
    assert enabled_from_config({}) is False
    assert plan_mode_enabled({}) is False


def test_gate_reads_stored_bool():
    assert enabled_from_config({SETTING_KEY: True}) is True
    assert enabled_from_config({SETTING_KEY: False}) is False


def test_gate_malformed_raises():
    for bad in ("yes", "on", 1, 0, None, [], {}):
        with pytest.raises(ValueError):
            enabled_from_config({SETTING_KEY: bad})


def test_set_enabled_and_gate_change():
    enabled, change = set_enabled({}, True)
    assert enabled is True
    assert change.event() == {
        "type": "plan_mode_setting_changed", "from": False, "to": True}
    record = change.record("sess-1", True)
    assert record["session_id"] == "sess-1"
    assert record["journaled"] is True
    assert format_gate_change(record) == "Plan mode is now on."
    assert format_gate_change(change.event()) == "Plan mode is now on."
    enabled, change = set_enabled({SETTING_KEY: True}, False)
    assert enabled is False
    assert format_gate_change(change.event()) == "Plan mode is now off."


def test_set_enabled_noop_and_non_bool_refuse():
    with pytest.raises(ValueError, match="already off"):
        set_enabled({}, False)
    with pytest.raises(ValueError, match="already on"):
        set_enabled({SETTING_KEY: True}, True)
    with pytest.raises(ValueError):
        set_enabled({}, "on")


# -- decide: the posture's mechanical judgement ------------------------------


def test_decide_in_posture_read_allowed_write_and_execute_denied():
    assert decide(True, "read") == "allow"
    assert decide(True, "write") == "deny"
    assert decide(True, "execute") == "deny"


def test_decide_out_of_posture_everything_allowed():
    for effect in EFFECTS:
        assert decide(False, effect) == "allow"


def test_decide_tool_kind_aliases():
    assert decide(True, "path_read") == "allow"
    assert decide(True, "path_write") == "deny"
    assert decide(True, "edit") == "deny"
    assert decide(True, "command") == "deny"
    assert decide(False, "command") == "allow"


def test_decide_unknown_effect_and_bad_posture_raise():
    with pytest.raises(ValueError):
        decide(True, "teleport")
    with pytest.raises(ValueError):
        decide(True, "")
    with pytest.raises(ValueError):
        decide("yes", "read")


# -- plan slices: Part IX form -------------------------------------------------


def test_validate_plan_slice_ok():
    slice_ = validate_plan_slice(_slice())
    assert isinstance(slice_, PlanSlice)
    assert slice_.title == "First slice"
    assert slice_.intent == "Do the first thing"
    assert slice_.what == "Do the first thing"
    assert slice_.acceptance_checks == ("the first thing works",)
    assert slice_.to_record() == {
        "title": "First slice", "intent": "Do the first thing",
        "acceptance_checks": ["the first thing works"]}


def test_validate_plan_slice_aliases_and_stripping():
    slice_ = validate_plan_slice(
        {"title": "  Named  ", "what": "Do it",
         "checks": ["  it works  "]})
    assert slice_.title == "Named"
    assert slice_.intent == "Do it"
    assert slice_.acceptance_checks == ("it works",)


def test_slice_blank_title_and_intent_raise():
    with pytest.raises(ValueError):
        validate_plan_slice(_slice(title="   "))
    with pytest.raises(ValueError):
        validate_plan_slice(_slice(title=""))
    with pytest.raises(ValueError):
        validate_plan_slice(_slice(intent="  "))
    with pytest.raises(ValueError):
        PlanSlice(title="", intent="x", acceptance_checks=("y",))


def test_slice_without_checks_raises():
    with pytest.raises(ValueError):
        validate_plan_slice(_slice(checks=()))
    with pytest.raises(ValueError):
        validate_plan_slice({"title": "T", "intent": "I"})
    with pytest.raises(ValueError):
        validate_plan_slice(_slice(checks=("  ",)))
    with pytest.raises(ValueError):
        validate_plan_slice(_slice(checks="one string is not a list"))
    with pytest.raises(ValueError):
        PlanSlice(title="T", intent="I", acceptance_checks=())


def test_slice_unknown_and_missing_keys_raise():
    with pytest.raises(ValueError):
        validate_plan_slice(dict(_slice(), telemetry="off"))
    spec = _slice()
    del spec["title"]
    with pytest.raises(ValueError):
        validate_plan_slice(spec)
    with pytest.raises(ValueError):
        validate_plan_slice("not a mapping")


# -- the whole plan --------------------------------------------------------------


def test_validate_plan_ok_and_record_round_trip():
    plan = _plan()
    assert isinstance(plan, Plan)
    assert plan.title == "Ship the thing"
    assert plan.approved is False
    assert plan.slice_count == 2
    assert plan.check_count == 3
    assert [s.title for s in plan.slices] == [
        "First slice", "Second slice"]
    assert validate_plan(plan.to_record()) == plan
    assert validate_plan(plan) is plan


def test_build_plan_from_pieces():
    plan = build_plan("T", "I", [_slice()])
    assert plan.slice_count == 1
    assert plan.slices[0].title == "First slice"


def test_empty_plan_raises():
    with pytest.raises(ValueError):
        _plan(slices=[])
    with pytest.raises(ValueError):
        validate_plan({"title": "T", "intent": "I"})
    with pytest.raises(ValueError):
        Plan(title="T", intent="I", slices=())


def test_plan_blank_title_and_intent_raise():
    with pytest.raises(ValueError):
        _plan(title="  ")
    with pytest.raises(ValueError):
        _plan(intent="")
    with pytest.raises(ValueError):
        _plan(title=None)


def test_plan_with_a_slice_without_checks_raises():
    bad = {"title": "Bad slice", "intent": "Do it",
           "acceptance_checks": []}
    with pytest.raises(ValueError):
        _plan(slices=[_slice(), bad])


def test_plan_unknown_key_and_bad_approved_raise():
    with pytest.raises(ValueError):
        _plan(extra="nope")
    with pytest.raises(ValueError):
        _plan(approved="yes")


# -- approval: the one gate to building -------------------------------------------


def test_unapproved_plan_cannot_build_in_posture():
    plan = _plan()
    assert can_build(True, plan) is False
    assert can_build(True, None) is False


def test_approved_plan_can_build_in_posture():
    plan = _plan()
    approved = approve(plan)
    assert approved.approved is True
    assert approved is not plan
    assert plan.approved is False
    assert can_build(True, approved) is True


def test_building_is_normal_out_of_posture():
    assert can_build(False, None) is True
    assert can_build(False, _plan()) is True
    assert can_build(False, approve(_plan())) is True


def test_approval_does_not_leak_between_plans():
    first = _plan()
    second = _plan(title="Another plan")
    approve(first)
    assert first.approved is False
    assert second.approved is False
    assert can_build(True, second) is False
    assert approve(second).approved is True
    assert first.approved is False


def test_approve_and_can_build_bad_inputs_raise():
    with pytest.raises(ValueError):
        approve({"title": "not a plan"})
    with pytest.raises(ValueError):
        can_build(True, {"title": "not a plan"})
    with pytest.raises(ValueError):
        can_build("yes", None)


# -- refusals, shaped as news -------------------------------------------------------


def test_refusal_record_shape_is_news():
    refusal = build_refusal(effect="write")
    assert isinstance(refusal, PlanRefusal)
    assert refusal.headline.startswith("Plan mode refusal:")
    record = refusal_record(effect="write")
    assert record["type"] == "plan_mode_refusal"
    assert record["slice"] == "M-100"
    assert record["news"] is True
    assert record["surface"] == "session_event"
    assert record["effect"] == "write"
    assert record["headline"] == refusal.headline
    assert format_refusal(refusal) == refusal.headline
    assert format_refusal(record) == refusal.headline
    with pytest.raises(ValueError):
        format_refusal({"type": "something_else"})


def test_refusal_for_effect_and_build():
    plan = _plan()
    assert refusal_for_effect(True, "write").effect == "write"
    assert refusal_for_effect(True, "execute").effect == "execute"
    with pytest.raises(ValueError):
        refusal_for_effect(True, "read")
    with pytest.raises(ValueError):
        refusal_for_effect(False, "write")
    refusal = refusal_for_build(True, plan)
    assert refusal.plan_title == "Ship the thing"
    assert "not approved" in refusal.reason
    assert refusal_for_build(True, None).plan_title is None
    with pytest.raises(ValueError):
        refusal_for_build(False, None)
    with pytest.raises(ValueError):
        refusal_for_build(True, approve(plan))


# -- the /plan surface -----------------------------------------------------------------


def test_parse_plan_args_actions():
    assert parse_plan_args("") == {"action": "show"}
    assert parse_plan_args("show") == {"action": "show"}
    assert parse_plan_args("status") == {"action": "show"}
    assert parse_plan_args("on") == {"action": "on"}
    assert parse_plan_args("off") == {"action": "off"}
    assert parse_plan_args("approve") == {"action": "approve"}
    assert parse_plan_args("build") == {"action": "build"}
    assert parse_plan_args("check read") == {
        "action": "check", "effect": "read"}
    assert parse_plan_args("check command") == {
        "action": "check", "effect": "execute"}


def test_parse_plan_args_errors():
    for bad in ("frobnicate", "check", "check teleport", "on please"):
        with pytest.raises(ValueError) as excinfo:
            parse_plan_args(bad)
        assert str(excinfo.value) == USAGE


def test_format_plan_status_is_one_line():
    plan = _plan()
    off = format_plan_status({}, plan)
    assert "\n" not in off
    assert off.startswith("Plan mode: off (plan_mode)")
    assert "building allowed" in off
    on = format_plan_status({SETTING_KEY: True}, plan)
    assert "\n" not in on
    assert on.startswith("Plan mode: on (plan_mode)")
    assert "unapproved" in on
    assert "building gated on approval" in on
    approved = format_plan_status({SETTING_KEY: True}, approve(plan))
    assert "approved" in approved
    assert "building allowed" in approved
    assert "no plan yet" in format_plan_status({SETTING_KEY: True})


def test_format_plan_renders_slices_in_order_with_checks():
    text = format_plan(_plan())
    assert text.startswith("Plan: Ship the thing (unapproved)")
    assert "Intent: Build the thing in slices" in text
    assert "1. First slice - Do the first thing" in text
    assert "2. Second slice - Do the second thing" in text
    assert "- the first thing works" in text
    assert "- the second thing is tested" in text
    assert text.index("First slice") < text.index("Second slice")
    assert format_plan(approve(_plan())).startswith(
        "Plan: Ship the thing (approved)")


def test_format_plan_mode_whole_slice():
    text = format_plan_mode({SETTING_KEY: True}, _plan())
    assert "M-100" in text
    assert PLAIN_EXPLANATION in text
    assert "Plan mode: on (plan_mode) - " in text
    assert "Plan: Ship the thing" in text
    assert text.endswith(USAGE)
    bare = format_plan_mode({})
    assert "Plan mode: off (plan_mode) - " in bare
    assert "no plan yet" in bare

# -- agent layer: status, set, held plan, checks, surfaces (M-100) ---

import copy as _copy

from mythic_agent.core import plan_mode as pm
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


def _spec(**overrides):
    spec = {
        "title": "Ship the thing",
        "intent": "Build the thing in slices",
        "slices": [_slice()],
    }
    spec.update(overrides)
    return spec


class TestPlanModeAgent:
    def test_status_defaults_off_no_plan(self, agent):
        status = agent.plan_mode_status()
        assert status["enabled"] is False
        assert status["plan"] is None
        assert status["screen"] == format_plan_mode(agent.config, None)
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["can_build"] is True
        assert agent.current_plan() is None

    def test_status_reflects_on_and_held_plan(self, agent):
        agent.config[SETTING_KEY] = True
        agent.set_current_plan(_spec())
        status = agent.plan_mode_status()
        assert status["enabled"] is True
        assert status["plan"]["title"] == "Ship the thing"
        assert status["plan"]["approved"] is False
        assert status["can_build"] is False
        agent.approve_current_plan()
        assert agent.plan_mode_status()["can_build"] is True

    def test_status_malformed_config_raises(self, agent):
        agent.config[SETTING_KEY] = "yes"
        with pytest.raises(ValueError):
            agent.plan_mode_status()

    def test_set_on_then_off(self, agent):
        record = agent.set_plan_mode(True)
        assert record["type"] == "plan_mode_setting_changed"
        assert record["from"] is False and record["to"] is True
        assert record["journaled"] is False
        assert agent.config[SETTING_KEY] is True
        assert format_gate_change(record) == "Plan mode is now on."
        record = agent.set_plan_mode(False)
        assert record["from"] is True and record["to"] is False
        assert format_gate_change(record) == "Plan mode is now off."

    def test_set_noop_refuses_and_changes_nothing(self, agent):
        with pytest.raises(ValueError, match="already off"):
            agent.set_plan_mode(False)
        assert SETTING_KEY not in agent.config
        with pytest.raises(ValueError):
            agent.set_plan_mode("on")

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.set_plan_mode(True)
        assert record["journaled"] is True
        events = _events(store, session_id, "plan_mode_setting_changed")
        assert len(events) == 1
        assert events[0]["from"] is False and events[0]["to"] is True
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        before = _copy.deepcopy(agent.config)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_plan_mode(True)
        assert agent.config == before
        assert SETTING_KEY not in agent.config
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["plan_mode_setting_changed",
                              "plan_mode_setting_reverted"]
        agent.close()

    def test_set_current_plan_validates_and_holds(self, agent):
        plan = agent.set_current_plan(_spec())
        assert isinstance(plan, Plan)
        assert agent.current_plan() is plan
        assert plan.approved is False
        with pytest.raises(ValueError):
            agent.set_current_plan(_spec(slices=[]))
        assert agent.current_plan() is plan
        held = agent.set_current_plan(_plan())
        assert held.title == "Ship the thing"

    def test_build_current_plan_from_pieces(self, agent):
        plan = agent.build_current_plan(
            "Built plan", "Build it", [_slice()])
        assert plan.title == "Built plan"
        assert agent.current_plan() is plan
        with pytest.raises(ValueError):
            agent.build_current_plan("T", "I", [])

    def test_approve_current_plan(self, agent):
        with pytest.raises(ValueError, match="no plan to approve"):
            agent.approve_current_plan()
        original = agent.set_current_plan(_spec())
        approved = agent.approve_current_plan()
        assert approved.approved is True
        assert original.approved is False
        assert agent.current_plan() is approved

    def test_approval_does_not_leak_into_the_next_plan(self, agent):
        agent.set_current_plan(_spec())
        agent.approve_current_plan()
        fresh = agent.set_current_plan(_spec(title="Another plan"))
        assert fresh.approved is False
        assert agent.plan_mode_status()["plan"]["approved"] is False

class TestCheckPlan:
    def test_read_allowed_publishes_nothing(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.config[SETTING_KEY] = True
        before = len(store.export(session_id)["events"])
        assert agent.check_plan_effect("read") == "allow"
        assert len(store.export(session_id)["events"]) == before
        assert _events(store, session_id, "plan_mode_refusal") == []
        agent.close()

    def test_write_denied_publishes_refusal_news(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.config[SETTING_KEY] = True
        assert agent.check_plan_effect("write") == "deny"
        events = _events(store, session_id, "plan_mode_refusal")
        assert len(events) == 1
        assert events[0]["news"] is True
        assert events[0]["surface"] == "session_event"
        assert events[0]["effect"] == "write"
        agent.close()

    def test_execute_alias_denied_as_execute(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.config[SETTING_KEY] = True
        assert agent.check_plan_effect("command") == "deny"
        events = _events(store, session_id, "plan_mode_refusal")
        assert len(events) == 1
        assert events[0]["effect"] == "execute"
        agent.close()

    def test_gate_off_computes_allow_and_publishes_nothing(
            self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        assert agent.check_plan_effect("write") == "allow"
        assert agent.check_plan_build() is True
        assert _events(store, session_id, "plan_mode_refusal") == []
        agent.close()

    def test_unknown_effect_raises(self, agent):
        agent.config[SETTING_KEY] = True
        with pytest.raises(ValueError):
            agent.check_plan_effect("teleport")

    def test_build_gated_without_a_plan_publishes_refusal(
            self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.config[SETTING_KEY] = True
        assert agent.check_plan_build() is False
        events = _events(store, session_id, "plan_mode_refusal")
        assert len(events) == 1
        assert events[0]["news"] is True
        assert events[0]["plan_title"] is None
        agent.close()

    def test_build_gated_on_unapproved_plan_publishes_refusal(
            self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.config[SETTING_KEY] = True
        agent.set_current_plan(_spec())
        assert agent.check_plan_build() is False
        events = _events(store, session_id, "plan_mode_refusal")
        assert len(events) == 1
        assert events[0]["plan_title"] == "Ship the thing"
        agent.close()

    def test_build_allowed_after_approval_publishes_nothing(
            self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.config[SETTING_KEY] = True
        agent.set_current_plan(_spec())
        agent.approve_current_plan()
        before = len(store.export(session_id)["events"])
        assert agent.check_plan_build() is True
        assert len(store.export(session_id)["events"]) == before
        assert _events(store, session_id, "plan_mode_refusal") == []
        agent.close()


class TestPlanTerminalSurface:
    def test_show_is_the_whole_slice(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/plan")
        assert "M-100" in text and "Plan mode: off (plan_mode)" in text

    def test_check_allowed_and_denied_headlines(self, agent):
        from mythic_agent.terminal import _slash
        _slash(agent, "/plan on")
        _, _, text = _slash(agent, "/plan check read")
        assert text.startswith("Plan allowed:")
        _, _, text = _slash(agent, "/plan check write")
        assert text.startswith("Plan mode refusal:")

    def test_build_gate_flow(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/plan build")
        assert text.startswith("Building allowed:")
        _slash(agent, "/plan on")
        _, _, text = _slash(agent, "/plan build")
        assert text.startswith("Plan mode refusal:")
        agent.set_current_plan(_spec())
        _, _, text = _slash(agent, "/plan approve")
        assert "Plan approved:" in text
        _, _, text = _slash(agent, "/plan build")
        assert text.startswith("Building allowed:")

    def test_approve_without_a_plan_is_a_plain_error(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/plan approve")
        assert "no plan to approve" in text

    def test_gate_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/plan on")
        assert text == "Plan mode is now on."
        assert agent.config[SETTING_KEY] is True
        _, _, text = _slash(agent, "/plan on")
        assert "already on" in text
        _, _, text = _slash(agent, "/plan off")
        assert text == "Plan mode is now off."

    def test_bad_grammar_is_the_usage(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/plan frobnicate")
        assert text == USAGE


@pytest.fixture()
def plan_handler(agent, monkeypatch):
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


def _plan_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPlanCommand:
    def test_show_is_default(self, plan_handler, agent):
        plan_handler._handle_plan("")
        text = _plan_published_text(plan_handler)
        assert "M-100" in text and "Plan mode: off" in text

    def test_check_denied_is_published(self, plan_handler, agent):
        agent.config[SETTING_KEY] = True
        plan_handler._handle_plan("check write")
        assert "Plan mode refusal:" in _plan_published_text(plan_handler)

    def test_approve_then_build_is_published(self, plan_handler, agent):
        agent.config[SETTING_KEY] = True
        agent.set_current_plan(_spec())
        plan_handler._handle_plan("approve")
        assert "Plan approved:" in _plan_published_text(plan_handler)
        plan_handler._handle_plan("build")
        assert "Building allowed:" in _plan_published_text(plan_handler)

    def test_gate_via_the_handler(self, plan_handler, agent):
        plan_handler._handle_plan("on")
        assert "now on" in _plan_published_text(plan_handler)
        assert agent.config[SETTING_KEY] is True

    def test_bad_grammar_is_published(self, plan_handler, agent):
        plan_handler._handle_plan("frobnicate")
        assert "Usage: /plan" in _plan_published_text(plan_handler)


class TestChatScreenRoutingPlan:
    def test_plan_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/plan off", _FakeLog())
        assert calls == [("/plan", "off")]
