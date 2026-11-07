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
