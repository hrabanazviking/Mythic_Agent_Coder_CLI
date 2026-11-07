"""M-116 - Approval by phone-sized moments.

TIER: unit (pure layer)

Covers the M-116 pure layer
(``mythic_agent.core.approval_moments``): a moment
held as validated data - one question, full context
(what, where, what it does) and choices that each
state their effect - a mechanical judge that derives
completeness from given data only, the session-news
record, the deterministic registry, and the shared
/moment parser + formatters. The agent layer is a
later step; nothing here wires the Agent, the
ToolPolicy ask road, TUI or terminal.
"""

from __future__ import annotations

import pytest

from mythic_agent.core.approval_moments import (
    APPROVAL_MOMENTS_SLICE,
    CHOICE_KEYS,
    MOMENT_CHAR_BUDGET,
    PLAIN_EXPLANATION,
    REQUIRED_PARTS,
    STATES,
    USAGE,
    ApprovalChoice,
    ApprovalMoment,
    ApprovalMomentRegistry,
    MomentAssessment,
    build_choice,
    build_moment,
    format_assessment,
    format_choice,
    format_moment,
    format_moment_record,
    format_moment_screen,
    format_parts,
    judge_moment,
    moment_record,
    normalize_choice_key,
    normalize_record_id,
    parse_moment_args,
    plain_words,
    validate_choice,
    validate_moment,
)

COMPLETE = {
    "what": "Run the test suite?",
    "where": "in this project, on this machine",
    "what_it_does": "runs every test and reports the failures",
    "choices": [
        {"key": "approve", "label": "Run it",
         "effect": "the test suite runs now"},
        {"key": "deny", "label": "Skip it",
         "effect": "nothing runs and the work waits"},
    ],
}


# -- vocabulary and moment data ---------------------------------------


def test_slice_and_vocabulary():
    assert APPROVAL_MOMENTS_SLICE == "M-116"
    assert REQUIRED_PARTS == ("what", "where", "what_it_does", "choices")
    assert STATES == ("complete", "incomplete")
    assert CHOICE_KEYS == ("approve", "deny")
    assert MOMENT_CHAR_BUDGET == 600
    assert "single, complete question" in PLAIN_EXPLANATION
    assert "full context" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /moment")


def test_choice_key_readings():
    assert normalize_choice_key("Approve") == "approve"
    assert normalize_choice_key(" run-now ") == "run-now"
    with pytest.raises(ValueError):
        normalize_choice_key("")
    with pytest.raises(ValueError):
        normalize_choice_key("two words")
    with pytest.raises(ValueError):
        normalize_choice_key(7)


def test_record_id_readings():
    assert normalize_record_id("approval-moment-1") == "approval-moment-1"
    with pytest.raises(ValueError):
        normalize_record_id("has space")
    with pytest.raises(ValueError):
        normalize_record_id("")


def test_choice_validation_and_aliases():
    choice = validate_choice(
        {"name": "approve", "label": "Run it", "does": "it runs"})
    assert choice == ApprovalChoice(
        key="approve", label="Run it", effect="it runs")
    assert validate_choice("deny") == ApprovalChoice(key="deny")
    assert build_choice("approve", "Run it", "it runs") == choice
    with pytest.raises(ValueError):
        validate_choice({"key": "approve", "bogus": 1})
    with pytest.raises(ValueError):
        validate_choice({"label": "no key"})
    with pytest.raises(ValueError):
        validate_choice({"key": "a", "name": "b"})
    with pytest.raises(ValueError):
        validate_choice(42)


def test_moment_validation_and_aliases():
    moment = validate_moment({
        "question": "Run the test suite?",
        "location": "in this project",
        "does": "runs every test",
        "choices": ["approve", "deny"],
    })
    assert moment.what == "Run the test suite?"
    assert moment.where == "in this project"
    assert moment.what_it_does == "runs every test"
    assert moment.choice_keys == ("approve", "deny")
    assert moment.question_count == 1
    with pytest.raises(ValueError):
        validate_moment({"what": "x", "bogus": 1})
    with pytest.raises(ValueError):
        validate_moment({"what": "x", "question": "y"})
    with pytest.raises(ValueError):
        validate_moment("not a mapping")
    with pytest.raises(ValueError):
        validate_moment({"choices": "approve"})


def test_moment_duplicate_choice_keys_refuse():
    with pytest.raises(ValueError):
        build_moment(choices=[{"key": "approve"}, {"key": "Approve"}])


def test_moment_question_count_readings():
    listed = validate_moment({"questions": ["One?", "Two?"]})
    assert listed.question_count == 2
    single = validate_moment({"questions": ["Only this?"]})
    assert single.what == "Only this?"
    with pytest.raises(ValueError):
        validate_moment({"questions": ["One?"], "question_count": 2})
    with pytest.raises(ValueError):
        build_moment(question_count=0)
    with pytest.raises(ValueError):
        build_moment(question_count=True)


def test_moment_is_frozen():
    moment = build_moment(what="Run it?")
    with pytest.raises(Exception):
        moment.what = "changed"  # type: ignore[misc]


# -- the judge ----------------------------------------------------------


def test_judge_complete_moment():
    assessment = judge_moment(COMPLETE)
    assert assessment.state == "complete"
    assert assessment.missing == ()
    assert assessment.moment.what == "Run the test suite?"
    assert any("full context" in line or "What is asked" in line
               for line in assessment.reasons)


def test_judge_empty_proposal_names_every_part():
    assessment = judge_moment({})
    assert assessment.state == "incomplete"
    assert assessment.missing == (
        "what", "where", "what_it_does", "choices")


def test_judge_bare_yes_no_is_never_complete():
    # The slice law: a bare yes/no stripped of context refuses.
    assessment = judge_moment({"choices": [
        {"key": "yes"}, {"key": "no"}]})
    assert assessment.state == "incomplete"
    assert "what" in assessment.missing
    assert "choice_effects" in assessment.missing


def test_judge_choice_without_effect_is_incomplete():
    proposal = dict(COMPLETE)
    proposal["choices"] = [
        {"key": "approve", "label": "Run it",
         "effect": "the test suite runs now"},
        {"key": "deny", "label": "Skip it"},
    ]
    assessment = judge_moment(proposal)
    assert assessment.state == "incomplete"
    assert assessment.missing == ("choice_effects",)
    assert any("deny" in line for line in assessment.reasons)


def test_judge_single_choice_is_incomplete():
    proposal = dict(COMPLETE)
    proposal["choices"] = [
        {"key": "approve", "label": "Run it", "effect": "it runs"}]
    assessment = judge_moment(proposal)
    assert "choices" in assessment.missing


def test_judge_multi_question_pileup_is_incomplete():
    proposal = dict(COMPLETE)
    proposal["what"] = "Run the tests? And commit the result?"
    assert "single_question" in judge_moment(proposal).missing
    listed = dict(COMPLETE)
    listed["questions"] = ["Run the tests?", "Commit the result?"]
    assert "single_question" in judge_moment(listed).missing


def test_judge_oversize_is_incomplete():
    proposal = dict(COMPLETE)
    proposal["what_it_does"] = "explains " + ("at great length " * 60)
    assessment = judge_moment(proposal)
    assert assessment.state == "incomplete"
    assert "phone_sized" in assessment.missing


def test_judge_reads_moment_objects_and_refuses_unknown_keys():
    moment = validate_moment(COMPLETE)
    assert judge_moment(moment).state == "complete"
    with pytest.raises(ValueError):
        judge_moment({"what": "x", "surprise": 1})
    with pytest.raises(ValueError):
        judge_moment(42)


def test_assessment_cannot_disagree_with_itself():
    moment = validate_moment(COMPLETE)
    with pytest.raises(ValueError):
        MomentAssessment(state="complete", moment=moment,
                         missing=("what",))
    with pytest.raises(ValueError):
        MomentAssessment(state="incomplete", moment=moment)
    with pytest.raises(ValueError):
        MomentAssessment(state="ready", moment=moment,
                         missing=("what",))
    with pytest.raises(ValueError):
        MomentAssessment(state="incomplete", moment=moment,
                         missing=("bogus",))


# -- plain words and the news record ------------------------------------


def test_plain_words_complete_restates_full_context():
    words = plain_words(judge_moment(COMPLETE))
    assert words.startswith("Approval moment: complete")
    assert "Run the test suite?" in words
    assert "in this project, on this machine" in words
    assert "runs every test" in words
    assert "the test suite runs now" in words


def test_plain_words_incomplete_names_missing():
    words = plain_words(judge_moment({}))
    assert words.startswith("Approval moment: incomplete")
    assert "what" in words and "choices" in words
    assert "not ready to ask" in words
    with pytest.raises(ValueError):
        plain_words("not an assessment")


def test_moment_record_is_session_news():
    record = moment_record(judge_moment(COMPLETE))
    assert record["type"] == "approval_moment"
    assert record["session_event"] == "approval_moment"
    assert record["news"] is True
    assert record["slice"] == "M-116"
    assert record["state"] == "complete"
    assert record["missing"] == []
    assert record["choice_keys"] == ["approve", "deny"]
    assert record["headline"].startswith("Approval moment: complete")
    with pytest.raises(ValueError):
        moment_record({"type": "approval_moment"})


# -- the registry ---------------------------------------------------------


def test_registry_deterministic_ids():
    registry = ApprovalMomentRegistry()
    first = registry.judge_and_register(COMPLETE)
    second = registry.judge_and_register({})
    assert first.record_id == "approval-moment-1"
    assert second.record_id == "approval-moment-2"
    assert len(registry) == 2
    assert registry.list_records() == (first, second)
    assert registry.get("approval-moment-1") is first
    assert registry.record("approval-moment-2")["state"] == "incomplete"


def test_registry_supplied_ids_skip_and_duplicate_refuses():
    registry = ApprovalMomentRegistry()
    supplied = judge_moment(COMPLETE)
    supplied = MomentAssessment(
        state=supplied.state,
        moment=ApprovalMoment(
            what=supplied.moment.what, where=supplied.moment.where,
            what_it_does=supplied.moment.what_it_does,
            choices=supplied.moment.choices,
            record_id="approval-moment-1"),
        missing=supplied.missing, reasons=supplied.reasons)
    assert registry.register(supplied).record_id == "approval-moment-1"
    fresh = registry.judge_and_register(COMPLETE)
    assert fresh.record_id == "approval-moment-2"
    with pytest.raises(ValueError):
        registry.register(supplied)
    with pytest.raises(KeyError):
        registry.get("approval-moment-99")
    with pytest.raises(ValueError):
        registry.register("not an assessment")


# -- formatters and the shared parser -------------------------------------


def test_format_choice_and_parts():
    text = format_choice({"key": "approve", "label": "Run it",
                          "effect": "the suite runs"})
    assert "approve: Run it." in text
    assert "does: the suite runs" in text
    bare = format_choice("deny")
    assert "not ready" in bare
    parts = format_parts()
    assert "4 required" in parts
    for part in REQUIRED_PARTS:
        assert part in parts


def test_format_moment_and_assessment():
    moment = validate_moment(COMPLETE)
    text = format_moment(moment)
    assert "Run the test suite?" in text
    assert "where: in this project" in text
    assessment_text = format_assessment(judge_moment({}))
    assert "incomplete" in assessment_text
    assert "missing: what, where, what_it_does, choices" in assessment_text
    with pytest.raises(ValueError):
        format_assessment(moment)


def test_format_screen_empty_and_held():
    empty = format_moment_screen()
    assert "no records held" in empty
    assert USAGE in empty
    registry = ApprovalMomentRegistry()
    registry.judge_and_register(COMPLETE)
    held = format_moment_screen(registry)
    assert "1 held" in held
    assert "approval-moment-1" in held
    with pytest.raises(ValueError):
        format_moment_screen(42)


def test_format_moment_record_headline():
    registry = ApprovalMomentRegistry()
    registry.judge_and_register(COMPLETE)
    record = registry.record("approval-moment-1")
    assert format_moment_record(record) == record["headline"]
    with pytest.raises(ValueError):
        format_moment_record({"type": "other"})


def test_parse_moment_args_grammar():
    assert parse_moment_args("") == ("show", None)
    assert parse_moment_args(None) == ("show", None)
    assert parse_moment_args("show") == ("show", None)
    assert parse_moment_args("parts") == ("parts", None)
    assert parse_moment_args("show approval-moment-1") == (
        "show", "approval-moment-1")
    assert parse_moment_args("approval-moment-1") == (
        "show", "approval-moment-1")
    for bad in ("show parts", "parts now", "show a b", "two words",
                "show !!"):
        with pytest.raises(ValueError):
            parse_moment_args(bad)
    with pytest.raises(ValueError):
        parse_moment_args(42)


def test_module_purity():
    import mythic_agent.core.approval_moments as module
    import inspect
    source = inspect.getsource(module)
    assert "import subprocess" not in source
    assert "from mythic_agent.agents" not in source
    assert "import os" not in source.split('"""', 2)[-1]
