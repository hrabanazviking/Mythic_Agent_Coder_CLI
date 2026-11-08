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


# -- agent layer -----------------------------------------------------------
#
# M-131 agent layer: the agent holds a
# ResearchSwarmRegistry for the session (session
# state only, no new setting), a swarm is recorded
# by being registered - published as its
# question_record / assignment_record /
# finding_record session news through the
# checkpoint road, deduped per piece id - the
# digest is published as ONE digest_record session
# event, deduped per digest, and the /swarm
# surface rides both roads on the pure parser +
# formatters. Status, find, swarm and digest reads
# register and publish nothing. This layer runs no
# research, calls no model, spawns no crew and
# claims no board - Part VIII does not exist yet,
# so the screen is where the digest is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _swarm_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestSwarmAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.swarm_status()
        assert status["question"] is None
        assert status["assignments"] == []
        assert status["findings"] == []
        assert status["swarm"]["leader"] == "cartographer"
        assert len(status["swarm"]["assignments"]) == 3
        assert len(status["swarm"]["findings"]) == 3
        assert status["digest"]["type"] == "swarm_digest"
        assert status["digest"]["complete"] is True
        assert "Research swarms (M-131)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._research_swarm_registry() is \
            agent._research_swarm_registry()
        assert agent._research_swarm_store is \
            agent._research_swarm_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.swarm_status()
        found = agent.find_swarm_findings("scribe")
        assert [f.member for f in found] == ["scribe"]
        assert agent.research_swarm().leader == "cartographer"
        digest = agent.swarm_digest()
        assert digest.complete is True
        assert digest.missing == ()
        registry = agent._research_swarm_registry()
        assert registry.list_assignments() == ()
        assert registry.list_findings() == ()
        for kind in ("swarm_question", "swarm_assignment",
                     "swarm_finding", "swarm_digest"):
            assert _swarm_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_pieces_raise_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_swarm_assignment("assignment-1")
        with pytest.raises(KeyError):
            agent.get_swarm_finding("finding-1")

    def test_find_member_without_a_finding_raises_keyerror(
            self, agent):
        with pytest.raises(KeyError):
            agent.find_swarm_findings("guardian")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_swarm_assignment(_assignment())
        agent.register_swarm_finding(_finding())
        status = agent.swarm_status()
        assert [a["member"] for a in status["assignments"]] == [
            "cartographer"]
        assert [f["member"] for f in status["findings"]] == [
            "cartographer"]
        # No question is held yet, so no digest can be
        # derived - the status says so plainly.
        assert status["question"] is None
        assert status["digest"] is None
        assert "docs - cartographer:" in status["screen"]
        assert len(status["swarm"]["assignments"]) == 3


class TestSwarmAgentRegister:
    def test_register_assignment_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_swarm_assignment(_assignment())
        assert outcome["assignment"]["assignment_id"] == \
            "assignment-1"
        assert outcome["record"]["type"] == "swarm_assignment"
        events = _swarm_events(store, session_id, "swarm_assignment")
        assert len(events) == 1
        assert events[0]["member"] == "cartographer"
        # The same record is never published twice.
        agent._publish_swarm_record(outcome["record"])
        assert len(_swarm_events(
            store, session_id, "swarm_assignment")) == 1
        # A foreign record type is refused on this road.
        agent._publish_swarm_record(
            digest_record(digest_swarm(load_research_swarm())))
        assert _swarm_events(store, session_id, "swarm_digest") \
            == []
        agent.close()

    def test_register_finding_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_swarm_assignment(_assignment())
        outcome = agent.register_swarm_finding(_finding())
        assert outcome["finding"]["finding_id"] == "finding-1"
        assert outcome["record"]["type"] == "swarm_finding"
        assert len(_swarm_events(
            store, session_id, "swarm_assignment")) == 1
        assert len(_swarm_events(
            store, session_id, "swarm_finding")) == 1
        agent._publish_swarm_record(outcome["record"])
        assert len(_swarm_events(
            store, session_id, "swarm_finding")) == 1
        agent.close()

    def test_register_finding_from_an_undealt_member_refuses(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValueError):
            agent.register_swarm_finding(
                _finding(member="guardian"))
        assert _swarm_events(store, session_id, "swarm_finding") \
            == []
        agent.close()

    def test_record_swarm_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_research_swarm()
        assert outcome["count"] == 7
        assert outcome["question"]["leader"] == "cartographer"
        assert len(outcome["assignments"]) == 3
        assert len(outcome["findings"]) == 3
        assert len(_swarm_events(
            store, session_id, "swarm_question")) == 1
        assert len(_swarm_events(
            store, session_id, "swarm_assignment")) == 3
        assert len(_swarm_events(
            store, session_id, "swarm_finding")) == 3
        assert agent.research_swarm().leader == "cartographer"
        agent.close()

    def test_record_same_swarm_twice_refuses(self, agent):
        agent.record_research_swarm()
        with pytest.raises(ValueError):
            agent.record_research_swarm()

    def test_swarm_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_swarm(tmp_path, _swarm_data())
        swarm = load_research_swarm_file(path)
        outcome = agent.record_research_swarm(swarm)
        assert outcome["count"] == 4
        assert agent.research_swarm().question.text == \
            "A later question?"
        assert agent.swarm_digest().missing == ("architect",)

    def test_find_prefers_the_held_pieces(self, agent):
        agent.register_swarm_assignment(_assignment())
        agent.register_swarm_finding(_finding())
        found = agent.find_swarm_findings("cartographer")
        assert [f.summary for f in found] == [
            "The docs say the road exists."]
        # The held pieces answer now: the example's
        # scribe finding no longer answers.
        with pytest.raises(KeyError):
            agent.find_swarm_findings("scribe")


class TestSwarmAgentDigest:
    def test_digest_report_publishes_one_digest_event(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.record_research_swarm()
        outcome = agent.report_swarm_digest()
        assert outcome["complete"] is True
        assert outcome["record"]["type"] == "swarm_digest"
        assert "Complete, on 3 source(s):" in outcome["screen"]
        digests = _swarm_events(store, session_id, "swarm_digest")
        # ONE digest event holds the whole answer.
        assert len(digests) == 1
        assert digests[0]["complete"] is True
        # Reporting again on the same findings publishes
        # nothing new.
        agent.report_swarm_digest()
        assert len(_swarm_events(
            store, session_id, "swarm_digest")) == 1
        # A newly held finding grows the digest: a new
        # digest announces as the new digest it is.
        agent.register_swarm_assignment(_assignment(
            member="forge_worker", focus="docs",
            brief="Read the forge notes."))
        agent.register_swarm_finding(_finding(
            member="forge_worker",
            summary="The forge adds a fourth reading.",
            sources=["docs/forge.md"]))
        outcome = agent.report_swarm_digest()
        assert "fourth reading" in outcome["record"]["answer"]
        assert len(_swarm_events(
            store, session_id, "swarm_digest")) == 2
        agent.close()

    def test_digest_report_with_a_member_still_out_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        swarm = load_research_swarm_file(
            _write_swarm(tmp_path, _swarm_data()))
        agent.record_research_swarm(swarm)
        outcome = agent.report_swarm_digest()
        assert outcome["complete"] is False
        assert outcome["record"]["missing"] == ["architect"]
        assert "Still out" in outcome["screen"]
        assert len(_swarm_events(
            store, session_id, "swarm_digest")) == 1
        agent.report_swarm_digest()
        assert len(_swarm_events(
            store, session_id, "swarm_digest")) == 1
        agent.close()

    def test_no_research_or_spawn_road_for_swarm(self, agent):
        # This layer holds the swarm as data: it runs
        # no research, calls no model, spawns no crew
        # and builds no board - Part VIII does not
        # exist yet, and the live fan-out is a later
        # road, not this slice.
        assert not hasattr(agent, "run_research_swarm")
        assert not hasattr(agent, "spawn_research_swarm")
        assert not hasattr(agent, "swarm_board")


class TestSwarmTerminalSurface:
    def test_show_digest_sources_and_kinds(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/swarm")
        assert "Research swarms (M-131)" in text
        _, _, text = _slash(agent, "/swarm show scribe")
        assert "Side by side" in text
        _, _, text = _slash(agent, "/swarm digest")
        assert "Complete, on 3 source(s):" in text
        assert "roadmap_slices.yaml" in text
        _, _, text = _slash(agent, "/swarm sources")
        assert "- mythic_agent/data/provider_registry.yaml" in text
        _, _, text = _slash(agent, "/swarm kinds")
        assert text == "Focus kinds: docs, options, comparison"

    def test_bare_member_shows_theirs(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/swarm architect")
        assert "architect:" in text
        assert "As options" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/swarm [show|show <member>|digest|sources|kinds]" \
            in text
        # A bare word parses as a member id (member ids
        # are slugs, not a fixed list), so an unknown
        # member answers with the find road's KeyError;
        # two stray words are a usage error.
        _, _, text = _slash(agent, "/swarm dance")
        assert "no finding from the member" in text
        _, _, text = _slash(agent, "/swarm dance party")
        assert text == USAGE


@pytest.fixture()
def swarm_handler(agent, monkeypatch):
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


def _swarm_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSwarmCommand:
    def test_show_is_default(self, swarm_handler, agent):
        swarm_handler._handle_swarm("")
        assert "Research swarms (M-131)" in \
            _swarm_published_text(swarm_handler)

    def test_show_one_digest_sources_and_kinds(
            self, swarm_handler, agent):
        swarm_handler._handle_swarm("show scribe")
        assert "Side by side" in _swarm_published_text(swarm_handler)
        swarm_handler._handle_swarm("digest")
        assert "Complete, on 3 source(s):" in \
            _swarm_published_text(swarm_handler)
        swarm_handler._handle_swarm("sources")
        assert "provider_registry.yaml" in \
            _swarm_published_text(swarm_handler)
        swarm_handler._handle_swarm("kinds")
        assert "Focus kinds:" in _swarm_published_text(swarm_handler)

    def test_bad_grammar_is_published(self, swarm_handler, agent):
        swarm_handler._handle_swarm("dance party")
        assert USAGE in _swarm_published_text(swarm_handler)


class TestChatScreenRoutingSwarm:
    def test_swarm_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/swarm kinds", _FakeLog())
        assert calls == [("/swarm", "kinds")]
