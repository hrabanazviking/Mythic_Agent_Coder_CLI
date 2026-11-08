"""M-131 Research swarms - pure-layer tests.

TIER: integration

The pure layer is the research formation as data:
one Cartographer-led question dealt out as
assignments (one member, one focus - the docs,
the options or the comparison - with a brief),
the findings the members return (a plain summary
standing on named sources), the shipped example
swarm held in a data file, a loader that reads a
swarm from any file, the digest derived
mechanically from the findings alone - complete
exactly when every assignment holds a finding,
its sources every source the findings cite - a
digest record shaped as session news, and a
registry. Nothing here runs research, calls a
model, opens a page, spawns a crew or claims a
Part VIII board: the swarm is data only, and the
findings arrive through later roads.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.research_swarms import (
    FOCUS_KINDS,
    PLAIN_EXPLANATION,
    SWARM_RESOURCE,
    SWARM_SCHEMA,
    SWARM_SLICE,
    USAGE,
    ResearchSwarm,
    ResearchSwarmRegistry,
    SwarmAssignment,
    SwarmDigest,
    SwarmFinding,
    SwarmQuestion,
    assignment_record,
    build_assignment,
    build_digest,
    build_finding,
    build_question,
    digest_plain_words,
    digest_record,
    digest_swarm,
    finding_record,
    format_digest,
    format_finding,
    format_findings,
    format_focus_kinds,
    format_swarm_screen,
    load_research_swarm,
    load_research_swarm_file,
    normalize_focus_kind,
    normalize_source,
    parse_swarm_args,
    plain_words,
    question_record,
    validate_assignment,
    validate_digest,
    validate_finding,
    validate_question,
    validate_swarm,
)

ROOT = Path(__file__).resolve().parents[1]


def _question(**kwargs):
    kwargs.setdefault("text", "A later question?")
    kwargs.setdefault("leader", "cartographer")
    return SwarmQuestion(**kwargs)


def _assignment(**kwargs):
    kwargs.setdefault("member", "cartographer")
    kwargs.setdefault("focus", "docs")
    kwargs.setdefault("brief", "Read the docs.")
    return SwarmAssignment(**kwargs)


def _finding(**kwargs):
    kwargs.setdefault("member", "cartographer")
    kwargs.setdefault("summary", "The docs say the road exists.")
    kwargs.setdefault("sources", ["docs/one.md"])
    return SwarmFinding(**kwargs)


def _swarm_data():
    return {
        "schema": SWARM_SCHEMA, "slice": SWARM_SLICE,
        "leader": "cartographer",
        "question": {"text": "A later question?",
                     "leader": "cartographer"},
        "assignments": [
            {"member": "cartographer", "focus": "docs",
             "brief": "Read the docs."},
            {"member": "architect", "focus": "options",
             "brief": "Weigh the options."},
        ],
        "findings": [
            {"member": "cartographer",
             "summary": "The docs say the road exists.",
             "sources": ["docs/one.md", "docs/two.md"]},
        ]}


def _write_swarm(tmp_path, data):
    path = tmp_path / "swarm.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------
# Constants, the shipped example, and its leader.
# ---------------------------------------------------------------------


def test_constants_and_usage():
    assert SWARM_SLICE == "M-131"
    assert SWARM_RESOURCE == "research_swarms.yaml"
    assert SWARM_SCHEMA == "mythic.research_swarms/1"
    assert FOCUS_KINDS == ("docs", "options", "comparison")
    assert USAGE.startswith("Usage: /swarm")
    assert "Cartographer-led" in PLAIN_EXPLANATION
    assert "board" in PLAIN_EXPLANATION


def test_shipped_example_swarm_shape():
    swarm = load_research_swarm()
    assert swarm.leader == "cartographer"
    assert swarm.question.leader == "cartographer"
    assert [(a.member, a.focus) for a in swarm.assignments] == [
        ("cartographer", "docs"), ("architect", "options"),
        ("scribe", "comparison")]
    assert [f.member for f in swarm.findings] == [
        "cartographer", "architect", "scribe"]
    assert swarm.is_complete()
    assert swarm.missing_members() == ()


def test_example_leader_is_the_shipped_cartographer():
    casting = load_casting()
    ids = [member.member_id for member in casting.members]
    assert load_research_swarm().leader in ids
    assert load_research_swarm().leader == "cartographer"


def test_example_digest_is_complete_with_ordered_sources():
    digest = digest_swarm(load_research_swarm())
    assert digest.complete is True
    assert digest.missing == ()
    assert digest.sources == (
        "mythic_agent/data/provider_registry.yaml",
        "mythic_agent/core/model_capabilities.py",
        "mythic_agent/data/roadmap_slices.yaml")
    swarm = load_research_swarm()
    for finding in swarm.findings:
        assert finding.summary in digest.answer


# ---------------------------------------------------------------------
# Normalizers and piece validation.
# ---------------------------------------------------------------------


def test_normalize_focus_kind_readings_and_refusals():
    assert normalize_focus_kind("Docs") == "docs"
    assert normalize_focus_kind("documentation") == "docs"
    assert normalize_focus_kind("choices") == "options"
    assert normalize_focus_kind("versus") == "comparison"
    with pytest.raises(ValueError):
        normalize_focus_kind("everything")
    with pytest.raises(ValueError):
        normalize_focus_kind("")


def test_normalize_source_refusals():
    assert normalize_source(" docs/one.md ") == "docs/one.md"
    with pytest.raises(ValueError):
        normalize_source("")
    with pytest.raises(ValueError):
        normalize_source("x" * 301)


def test_question_validation_and_two_spellings_refusal():
    question = validate_question(
        {"question": "Words?", "led_by": "cartographer"})
    assert question.text == "Words?"
    assert question.leader == "cartographer"
    with pytest.raises(ValueError):
        validate_question({"text": "One?", "question": "Two?",
                           "leader": "cartographer"})
    with pytest.raises(ValueError):
        validate_question({"text": "Words?", "leader": "cartographer",
                           "bogus": 1})
    with pytest.raises(ValueError):
        validate_question({"leader": "cartographer"})
    assert build_question(text="Built?", leader="scribe").leader == "scribe"
    assert plain_words(_question()).startswith("Led by cartographer:")


def test_assignment_validation():
    assignment = validate_assignment(
        {"member_id": "architect", "kind": "choices",
         "note": "Weigh them."})
    assert assignment.member == "architect"
    assert assignment.focus == "options"
    assert assignment.brief == "Weigh them."
    assert build_assignment(member="scribe", focus="docs",
                            brief="Read.").member == "scribe"
    with pytest.raises(ValueError):
        validate_assignment({"member": "scribe", "focus": "all",
                             "brief": "Read."})


def test_finding_validation_and_source_rules():
    finding = validate_finding(
        {"member": "scribe", "finding": "It compares so.",
         "source": "docs/one.md"})
    assert finding.sources == ("docs/one.md",)
    with pytest.raises(ValueError):
        validate_finding({"member": "scribe", "summary": "None.",
                          "sources": []})
    with pytest.raises(ValueError):
        _finding(sources=["a.md", "a.md"])
    with pytest.raises(ValueError):
        validate_finding({"member": "scribe", "summary": "One.",
                          "sources": ["a.md"], "source": "b.md"})


# ---------------------------------------------------------------------
# Whole-swarm validation and the digest judge.
# ---------------------------------------------------------------------


def test_swarm_validation_and_incomplete_digest():
    swarm = validate_swarm(_swarm_data())
    assert not swarm.is_complete()
    assert swarm.missing_members() == ("architect",)
    digest = digest_swarm(swarm)
    assert digest.complete is False
    assert digest.missing == ("architect",)
    assert digest.sources == ("docs/one.md", "docs/two.md")
    assert "Still out" in digest_plain_words(digest)


def test_swarm_refusals():
    data = _swarm_data()
    data["leader"] = "scribe"
    with pytest.raises(ValidationError):
        validate_swarm(data)
    data = _swarm_data()
    data["assignments"].append(
        {"member": "architect", "focus": "docs", "brief": "Again."})
    with pytest.raises(ValidationError):
        validate_swarm(data)
    data = _swarm_data()
    data["findings"].append(
        {"member": "scribe", "summary": "Undealt.",
         "sources": ["x.md"]})
    with pytest.raises(ValidationError):
        validate_swarm(data)
    data = _swarm_data()
    data["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_swarm(data)
    data = _swarm_data()
    data["assignments"] = []
    with pytest.raises(ValidationError):
        validate_swarm(data)


def test_digest_is_derived_never_stored():
    swarm = validate_swarm(_swarm_data())
    derived = digest_swarm(swarm)
    assert validate_digest(derived, swarm) == derived
    stored = build_digest(
        question=derived.question, answer="A stored claim.",
        sources=derived.sources, complete=False,
        missing=("architect",))
    with pytest.raises(ValueError):
        validate_digest(stored, swarm)
    with pytest.raises(ValueError):
        SwarmDigest(question="Q?", answer="A.", complete=True,
                    missing=("architect",))


def test_swarm_file_loader(tmp_path):
    swarm = load_research_swarm_file(_write_swarm(tmp_path, _swarm_data()))
    assert swarm.question.text == "A later question?"
    assert not swarm.is_complete()
    bad = _swarm_data()
    bad["findings"] = [{"member": "guardian", "summary": "No.",
                         "sources": ["x.md"]}]
    with pytest.raises(ValidationError):
        load_research_swarm_file(_write_swarm(tmp_path, bad))
    with pytest.raises(FileNotFoundError):
        load_research_swarm_file(tmp_path / "missing.yaml")


def test_swarm_lookups():
    swarm = load_research_swarm()
    assert swarm.assignment_for("architect").focus == "options"
    assert swarm.finding_for("scribe").member == "scribe"
    with pytest.raises(KeyError):
        swarm.assignment_for("guardian")
    with pytest.raises(KeyError):
        validate_swarm(_swarm_data()).finding_for("architect")


# ---------------------------------------------------------------------
# The registry.
# ---------------------------------------------------------------------


def test_registry_holds_and_digests():
    registry = ResearchSwarmRegistry()
    registry.hold_question(_question())
    first = registry.register_assignment(_assignment())
    second = registry.register_assignment(_assignment(
        member="architect", focus="options", brief="Weigh."))
    assert first.assignment_id == "assignment-1"
    assert second.assignment_id == "assignment-2"
    held = registry.register_finding(_finding())
    assert held.finding_id == "finding-1"
    assert registry.get_assignment("assignment-1") == first
    assert registry.get_finding("finding-1") == held
    assert registry.assignments_for("architect") == (second,)
    assert registry.findings_for("cartographer") == (held,)
    digest = registry.digest()
    assert digest.complete is False
    assert digest.missing == ("architect",)
    with pytest.raises(KeyError):
        registry.get_assignment("assignment-9")


def test_registry_refusals():
    registry = ResearchSwarmRegistry(_question())
    with pytest.raises(ValueError):
        registry.hold_question(_question())
    registry.register_assignment(_assignment())
    with pytest.raises(ValueError):
        registry.register_assignment(_assignment(focus="options"))
    with pytest.raises(ValueError):
        registry.register_finding(_finding(member="guardian"))
    registry.register_finding(_finding())
    with pytest.raises(ValueError):
        registry.register_finding(_finding(summary="Twice."))


def test_registry_register_swarm_round_trip():
    registry = ResearchSwarmRegistry()
    swarm = registry.register_swarm(load_research_swarm())
    assert swarm.is_complete()
    assert registry.digest().complete is True
    with pytest.raises(ValueError):
        registry.register_swarm(load_research_swarm())


# ---------------------------------------------------------------------
# Records, formatters, parser, purity.
# ---------------------------------------------------------------------


def test_records_are_session_news():
    question = question_record(_question())
    assert question["type"] == "swarm_question"
    assert question["news"] is True
    assert question["slice"] == "M-131"
    assignment = assignment_record(_assignment())
    assert assignment["type"] == "swarm_assignment"
    assert "dealt" in assignment["headline"]
    finding = finding_record(_finding())
    assert finding["type"] == "swarm_finding"
    assert finding["sources"] == ["docs/one.md"]
    record = digest_record(digest_swarm(load_research_swarm()))
    assert record["type"] == "swarm_digest"
    assert record["complete"] is True
    assert "complete" in record["headline"]


def test_formatters_and_screen():
    swarm = load_research_swarm()
    line = format_finding(swarm.findings[0])
    assert line.startswith("cartographer:")
    assert "provider_registry.yaml" in line
    findings_text = format_findings(validate_swarm(_swarm_data()))
    assert "still out" in findings_text
    digest_text = format_digest(swarm)
    assert "Complete" in digest_text
    assert "roadmap_slices.yaml" in digest_text
    assert format_focus_kinds() == "Focus kinds: docs, options, comparison"
    screen = format_swarm_screen()
    assert "Research swarms (M-131)" in screen
    assert USAGE in screen


def test_parser_grammar():
    assert parse_swarm_args("") == ("show", None)
    assert parse_swarm_args(None) == ("show", None)
    assert parse_swarm_args("show") == ("show", None)
    assert parse_swarm_args("show architect") == ("show", "architect")
    assert parse_swarm_args("architect") == ("show", "architect")
    assert parse_swarm_args("digest") == ("digest", None)
    assert parse_swarm_args("sources") == ("sources", None)
    assert parse_swarm_args("kinds") == ("kinds", None)
    with pytest.raises(ValueError):
        parse_swarm_args("digest now please")
    with pytest.raises(ValueError):
        parse_swarm_args(42)


def test_module_purity():
    source = (ROOT / "mythic_agent" / "core"
              / "research_swarms.py").read_text(encoding="utf-8")
    assert "agents.llm" not in source
    assert "import subprocess" not in source
    assert "requests" not in source
    assert "ui.screens" not in source
