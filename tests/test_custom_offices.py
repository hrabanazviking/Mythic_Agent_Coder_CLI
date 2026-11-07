"""M-123 Custom offices - pure-layer tests.

TIER: integration

The pure layer is custom offices as data: a
user-defined office definition (duties, tools,
inputs, outputs, hand-off contracts) validated
with M-122's own contract machinery, the shipped
examples book (the roadmap's Gatekeeper and
Benchmarker) held in a data file, a loader that
reads a book from any file, hand-off contracts
validated as a closed graph over the custom
offices in the book plus the six formalised
offices, a custom office record shaped as session
news, and a registry. A custom office never
collides with or overrides a shipped office.
Nothing here spawns an agent or runs a model.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.custom_offices import (
    CUSTOM_OFFICES_RESOURCE,
    CUSTOM_OFFICES_SCHEMA,
    CUSTOM_OFFICES_SLICE,
    EXAMPLE_CUSTOM_OFFICES,
    PLAIN_EXPLANATION,
    USAGE,
    CustomHandoffContract,
    CustomOfficeDefinition,
    CustomOfficeRegistry,
    CustomOfficesBook,
    build_custom_office,
    custom_office_record,
    example_custom_office_ids,
    format_custom_office,
    format_custom_offices,
    format_custom_offices_screen,
    is_custom_office_id,
    load_custom_offices,
    load_custom_offices_file,
    normalize_custom_office,
    normalize_handoff_target,
    parse_custom_offices_args,
    plain_words,
    validate_custom_office,
    validate_custom_offices,
)
from mythic_agent.core.offices import FORMAL_OFFICES, build_office, load_offices
from mythic_agent.core.role_routing import get_office, office_ids
from mythic_agent.core.tool_schemas import get_agent_tools
from mythic_agent.core.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def _office(**kwargs):
    kwargs.setdefault("office", "gatekeeper")
    kwargs.setdefault("title", "Gatekeeper")
    kwargs.setdefault("focus", "security review")
    kwargs.setdefault("purpose", "Review work for security risks.")
    kwargs.setdefault("duties", ["Review the change.", "Give a gate verdict."])
    kwargs.setdefault("tools", ["read_file", "run_command"])
    kwargs.setdefault("inputs", ["a built change"])
    kwargs.setdefault("outputs", ["a gate verdict"])
    kwargs.setdefault("handoffs", [{
        "to": "auditor", "artifact": "the findings",
        "condition": "every risk is named"}])
    return CustomOfficeDefinition(**kwargs)


def _book_data():
    return {
        "schema": CUSTOM_OFFICES_SCHEMA, "slice": CUSTOM_OFFICES_SLICE,
        "offices": [
            {"id": "gatekeeper", "title": "Gatekeeper",
             "focus": "security review",
             "purpose": "Review work for security risks.",
             "duties": ["Review the change."], "tools": ["read_file"],
             "inputs": ["a built change"], "outputs": ["a gate verdict"],
             "handoffs": [{"to": "auditor", "artifact": "the findings",
                           "condition": "every risk is named"}]},
            {"id": "benchmarker", "title": "Benchmarker",
             "focus": "benchmarking & measurement",
             "purpose": "Measure work and report the numbers.",
             "duties": ["Run the benchmarks."], "tools": ["run_command"],
             "inputs": ["a built change"], "outputs": ["a report"],
             "handoffs": [{"to": "gatekeeper", "artifact": "the change",
                           "condition": "the numbers are this change's"}]},
        ]}


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert CUSTOM_OFFICES_SLICE == "M-123"
    assert CUSTOM_OFFICES_SCHEMA == "mythic.custom_offices/1"
    assert CUSTOM_OFFICES_RESOURCE == "custom_offices.yaml"
    assert USAGE.startswith("Usage: /offices custom")
    assert "handoffs" in USAGE and "contract" in USAGE
    assert "Gatekeeper" in PLAIN_EXPLANATION
    assert "Benchmarker" in PLAIN_EXPLANATION
    assert "not formalised" in PLAIN_EXPLANATION or \
        "user-defined" in PLAIN_EXPLANATION


def test_examples_are_the_roadmaps_two():
    assert example_custom_office_ids() == ("gatekeeper", "benchmarker")
    assert EXAMPLE_CUSTOM_OFFICES == example_custom_office_ids()
    for office in EXAMPLE_CUSTOM_OFFICES:
        assert office not in office_ids()
        assert office not in FORMAL_OFFICES


def test_word_readings():
    assert normalize_custom_office("Gatekeeper") == "gatekeeper"
    assert normalize_custom_office(" bench-marker ") == "bench_marker"
    assert normalize_custom_office("REVIEWER_2") == "reviewer_2"
    assert is_custom_office_id("gatekeeper")
    assert not is_custom_office_id("auditor")
    assert not is_custom_office_id("")


def test_no_collision_with_any_shipped_office():
    for bad in list(FORMAL_OFFICES) + ["polymath", "guardian",
                                       "primary", "Primary", "Skald"]:
        with pytest.raises(ValueError):
            normalize_custom_office(bad)
    for bad in ("", "  ", "2reviewer", "review er", "review.er",
                None, 4):
        with pytest.raises(ValueError):
            normalize_custom_office(bad)


def test_handoff_target_readings():
    assert normalize_handoff_target("Auditor") == "auditor"
    assert normalize_handoff_target("Forge-Worker") == "forge_worker"
    assert normalize_handoff_target("gatekeeper") == "gatekeeper"
    for bad in ("polymath", "guardian", "primary", "", None):
        with pytest.raises(ValueError):
            normalize_handoff_target(bad)


# -- the shipped book: the roadmap's examples --------------------------------


def test_shipped_book_loads_and_holds_the_examples():
    book = load_custom_offices()
    assert isinstance(book, CustomOfficesBook)
    assert [d.office for d in book.definitions] == list(EXAMPLE_CUSTOM_OFFICES)
    assert book.custom_note
    assert "Gatekeeper" in book.custom_note
    assert "not" in book.custom_note and "six" in book.custom_note
    rebuilt = {"schema": CUSTOM_OFFICES_SCHEMA,
               "slice": CUSTOM_OFFICES_SLICE,
               "offices": [{
                   "id": d.office, "title": d.title, "focus": d.focus,
                   "purpose": d.purpose, "duties": list(d.duties),
                   "tools": list(d.tools), "inputs": list(d.inputs),
                   "outputs": list(d.outputs),
                   "handoffs": [c.to_record() for c in d.handoffs]}
                   for d in book.definitions]}
    assert validate_custom_offices(rebuilt, require_examples=True) == []


def test_examples_carry_the_roadmap_charges():
    book = load_custom_offices()
    gatekeeper = book.get("gatekeeper")
    assert gatekeeper.title == "Gatekeeper"
    assert gatekeeper.focus == "security review"
    benchmarker = book.get("benchmarker")
    assert benchmarker.title == "Benchmarker"
    assert "benchmark" in benchmarker.focus
    for definition in book.definitions:
        assert len(definition.duties) >= 3
        assert definition.inputs and definition.outputs


def test_example_tools_are_shipped_tool_names():
    book = load_custom_offices()
    shipped_tools = {t["function"]["name"] for t in get_agent_tools()}
    for definition in book.definitions:
        for tool in definition.tools:
            assert tool in shipped_tools


def test_example_handoff_graph_is_closed():
    book = load_custom_offices()
    pairs = {(d.office, c.to_office)
             for d in book.definitions for c in d.handoffs}
    assert pairs == {
        ("gatekeeper", "auditor"), ("gatekeeper", "forge_worker"),
        ("benchmarker", "auditor"), ("benchmarker", "gatekeeper")}
    for definition in book.definitions:
        assert definition.handoffs
        for contract in definition.handoffs:
            assert contract.artifact and contract.condition
            assert contract.to_office in FORMAL_OFFICES or \
                contract.to_office in EXAMPLE_CUSTOM_OFFICES
    assert book.contract("benchmarker", "gatekeeper").artifact
    assert book.contract("gatekeeper", "auditor").artifact
    assert book.handoffs_to("auditor")
    assert book.handoffs_to("gatekeeper")
    with pytest.raises(KeyError):
        book.contract("gatekeeper", "benchmarker")
    with pytest.raises(ValueError):
        book.get("auditor")
    with pytest.raises(KeyError):
        book.get("reviewer")


# -- definition construction and refusals -------------------------------------


def test_definition_construction_and_record():
    office = _office()
    record = office.to_record()
    assert record["type"] == "custom_office"
    assert record["slice"] == "M-123"
    assert record["office"] == "gatekeeper"
    assert record["formal"] is False and record["custom"] is True
    assert record["handoffs"][0]["to"] == "auditor"
    assert office.contract_to("auditor").artifact == "the findings"
    assert office.contract_to("Auditor").artifact == "the findings"
    with pytest.raises(KeyError):
        office.contract_to("scribe")
    contract = CustomHandoffContract(
        to_office="Forge-Worker", artifact="a", condition="b")
    assert contract.to_office == "forge_worker"
    custom = CustomHandoffContract(
        to_office="Bench-Marker", artifact="a", condition="b")
    assert custom.to_office == "bench_marker"


def test_definition_refusals():
    for bad_office in ("auditor", "skald", "polymath", "guardian",
                       "primary"):
        with pytest.raises(ValueError):
            _office(office=bad_office)
    with pytest.raises(ValueError):
        _office(title=" ")
    with pytest.raises(ValueError):
        _office(duties=[])
    with pytest.raises(ValueError):
        _office(duties=["Review.", "Review."])
    with pytest.raises(ValueError):
        _office(tools=[])
    with pytest.raises(ValueError):
        _office(tools="read_file")
    with pytest.raises(ValueError):
        _office(tools=["read_file", "read_file"])
    with pytest.raises(ValueError):
        _office(tools=["read file"])
    with pytest.raises(ValueError):
        _office(inputs=[])
    with pytest.raises(ValueError):
        _office(outputs=[" "])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "gatekeeper", "artifact": "x",
                           "condition": "y"}])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "auditor", "artifact": "x",
                           "condition": "y"},
                          {"to": "auditor", "artifact": "z",
                           "condition": "w"}])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "polymath", "artifact": "x",
                           "condition": "y"}])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "auditor", "artifact": "x"}])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "auditor", "artifact": "x",
                           "condition": "y", "speed": "fast"}])


def test_mapping_aliases_and_two_spellings_refusal():
    data = {"id": "gatekeeper", "title": "Gatekeeper",
            "focus": "security review",
            "purpose": "Review work for security risks.",
            "duties": ["Review."], "tools": ["read_file"],
            "inputs": ["a change"], "outputs": ["a verdict"],
            "handoffs": []}
    assert validate_custom_office(data).office == "gatekeeper"
    assert build_custom_office(data).office == "gatekeeper"
    both_same = dict(data, office="gatekeeper")
    assert validate_custom_office(both_same).office == "gatekeeper"
    with pytest.raises(ValueError):
        validate_custom_office(dict(data, office="benchmarker"))
    with pytest.raises(ValueError):
        validate_custom_office(dict(data, rank="first"))
    with pytest.raises(ValueError):
        validate_custom_office(
            {k: v for k, v in data.items() if k != "duties"})
    with pytest.raises(ValueError):
        validate_custom_office("gatekeeper")
    built = build_custom_office(
        office="reviewer", title="Reviewer", focus="review",
        purpose="Review things.", duties=["Review."],
        tools=["read_file"], inputs=["a change"],
        outputs=["findings"], handoffs=[])
    assert built.office == "reviewer"


def test_formalised_office_refuses_as_custom():
    formal = build_office({
        "id": "auditor", "title": "Auditor", "focus": "verify",
        "purpose": get_office("auditor").purpose,
        "duties": ["Check."], "tools": ["read_file"],
        "inputs": ["a change"], "outputs": ["a verdict"],
        "handoffs": []})
    with pytest.raises(ValueError):
        validate_custom_office(formal)
    with pytest.raises(ValueError):
        build_custom_office(formal)
    with pytest.raises(ValueError):
        CustomOfficeRegistry().register(formal)


# -- book validation and file loading ------------------------------------------


def test_book_refusals():
    good = _book_data()
    assert validate_custom_offices(good) == []
    assert validate_custom_offices(good, require_examples=True) == []
    assert validate_custom_offices("nope") != []
    assert validate_custom_offices(dict(good, schema="mythic.other/9")) != []
    assert validate_custom_offices(dict(good, slice="M-999")) != []
    assert validate_custom_offices(dict(good, offices=[])) != []
    assert validate_custom_offices(dict(good, extra=1)) != []
    doubled = _book_data()
    doubled["offices"] = doubled["offices"] + [doubled["offices"][0]]
    assert any("duplicate" in p for p in validate_custom_offices(doubled))
    dangling = _book_data()
    dangling["offices"] = dangling["offices"][1:]
    assert any("neither a formalised office" in p
               for p in validate_custom_offices(dangling))
    formal_entry = _book_data()
    formal_entry["offices"][0] = dict(
        formal_entry["offices"][0], id="auditor")
    assert validate_custom_offices(formal_entry) != []
    not_examples = validate_custom_offices(
        {"schema": CUSTOM_OFFICES_SCHEMA, "slice": CUSTOM_OFFICES_SLICE,
         "offices": _book_data()["offices"][:1]}, require_examples=True)
    assert any("example" in p for p in not_examples)
    with pytest.raises(ValidationError):
        load_custom_offices(dict(good, schema="mythic.other/9"))


def _write_book(tmp_path, data):
    path = tmp_path / "custom_offices.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_load_custom_offices_file_roundtrip(tmp_path):
    book = load_custom_offices_file(_write_book(tmp_path, _book_data()))
    assert [d.office for d in book.definitions] == [
        "gatekeeper", "benchmarker"]
    assert book.contract("benchmarker", "gatekeeper").condition == \
        "the numbers are this change's"
    assert book.contract("gatekeeper", "auditor").artifact == "the findings"


def test_load_custom_offices_file_single_new_office(tmp_path):
    data = {"schema": CUSTOM_OFFICES_SCHEMA, "slice": CUSTOM_OFFICES_SLICE,
            "offices": [
                {"id": "reviewer", "title": "Reviewer",
                 "focus": "careful review",
                 "purpose": "Review work carefully.",
                 "duties": ["Review."], "tools": ["read_file"],
                 "inputs": ["a change"], "outputs": ["findings"],
                 "handoffs": [{"to": "scribe", "artifact": "findings",
                               "condition": "they are written down"}]}]}
    book = load_custom_offices_file(_write_book(tmp_path, data))
    assert [d.office for d in book.definitions] == ["reviewer"]
    assert book.contract("reviewer", "scribe").artifact == "findings"


def test_load_custom_offices_file_refusals(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_custom_offices_file(tmp_path / "missing.yaml")
    bad = _write_book(tmp_path, {"schema": "x", "offices": "nope"})
    with pytest.raises(ValidationError):
        load_custom_offices_file(bad)
    malformed = tmp_path / "broken.yaml"
    malformed.write_text("offices: [unclosed\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_custom_offices_file(malformed)
    formal_office = _book_data()
    formal_office["offices"][0]["id"] = "auditor"
    with pytest.raises(ValidationError):
        load_custom_offices_file(_write_book(tmp_path, formal_office))


# -- registry, news record, plain words, formatters, parser -------------------


def test_registry_holds_the_book_and_refuses_duplicates():
    registry = CustomOfficeRegistry()
    held = registry.register_book(load_custom_offices())
    assert [d.office for d in held] == list(EXAMPLE_CUSTOM_OFFICES)
    assert registry.get("Gatekeeper").office == "gatekeeper"
    assert registry.list_definitions() == held
    with pytest.raises(ValueError):
        registry.register(held[0])
    with pytest.raises(KeyError):
        CustomOfficeRegistry().get("gatekeeper")
    with pytest.raises(ValueError):
        registry.get("auditor")
    with pytest.raises(ValueError):
        registry.register_book("not a book")
    with pytest.raises(ValueError):
        registry.register_book(load_offices())


def test_custom_office_record_is_session_news():
    record = custom_office_record(load_custom_offices().get("gatekeeper"))
    assert record["news"] is True
    assert record["type"] == "custom_office"
    assert record["slice"] == "M-123"
    assert record["office"] == "gatekeeper"
    assert record["formal"] is False and record["custom"] is True
    assert "Gatekeeper" in record["headline"]


def test_plain_words_and_formatters():
    book = load_custom_offices()
    words = plain_words(book.get("benchmarker"))
    assert "Benchmarker" in words and "benchmark" in words
    assert "gatekeeper" in words
    assert format_custom_office(book.get("gatekeeper")).startswith(
        "  gatekeeper:")
    text = format_custom_offices(book)
    assert text.startswith("Custom offices: 2 defined.")
    assert format_custom_offices() == (
        "Custom offices: none. No custom offices are defined.")
    assert format_custom_offices(CustomOfficeRegistry()) == (
        "Custom offices: none. No custom offices are defined.")
    screen = format_custom_offices_screen(book)
    assert "M-123" in screen and USAGE in screen
    with pytest.raises(ValueError):
        format_custom_offices("gatekeeper")


def test_parser():
    assert parse_custom_offices_args("") == ("show", None)
    assert parse_custom_offices_args(None) == ("show", None)
    assert parse_custom_offices_args("show") == ("show", None)
    assert parse_custom_offices_args("list") == ("show", None)
    assert parse_custom_offices_args("show Gatekeeper") == (
        "show", "gatekeeper")
    assert parse_custom_offices_args("benchmarker") == (
        "show", "benchmarker")
    assert parse_custom_offices_args("handoffs gatekeeper") == (
        "handoffs", "gatekeeper")
    assert parse_custom_offices_args("contract gatekeeper auditor") == (
        "contract", ("gatekeeper", "auditor"))
    assert parse_custom_offices_args("contract benchmarker gatekeeper") == (
        "contract", ("benchmarker", "gatekeeper"))
    # A bare valid custom id parses - the custom namespace is open,
    # so existence is the book / registry's judgement, not the
    # parser's; a malformed phrase still refuses.
    assert parse_custom_offices_args("dance") == ("show", "dance")
    for bad in ("show auditor", "show polymath", "handoffs",
                "contract gatekeeper", "contract auditor scribe",
                "contract gatekeeper polymath", "show a b",
                "dance party", 4):
        with pytest.raises(ValueError):
            parse_custom_offices_args(bad)


def test_module_purity():
    source = (ROOT / "mythic_agent" / "core" / "custom_offices.py").read_text(
        encoding="utf-8")
    for banned in ("agents.llm", "terminal", "command_handler"):
        assert banned not in source
    assert "from .offices import" in source


# -- agent layer -----------------------------------------------------------
#
# M-123 agent layer: the agent holds a
# CustomOfficeRegistry for the session (session
# state only, no new setting), a custom office is
# held by being registered or by a book being
# loaded - published as its custom_office_record
# session news through the checkpoint road, deduped
# per office id - and the /offices custom surface
# rides both roads on the pure parser + formatters.
# Status, hand-off and contract reads register and
# publish nothing. A custom office is a user-defined
# role, not a formalised office and not a cast
# member, so no spawn road is owed or built.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _custom_events(store, session_id):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == "custom_office"]


class TestCustomOfficesAgentStatus:
    def test_status_starts_unheld_but_shows_the_book(self, agent):
        status = agent.custom_offices_status()
        assert status["offices"] == []
        assert [d["office"] for d in status["book"]] == list(
            EXAMPLE_CUSTOM_OFFICES)
        assert "Custom offices: 2 defined." in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
        for record in status["book"]:
            assert record["formal"] is False
            assert record["custom"] is True

    def test_registry_is_one_per_agent(self, agent):
        assert agent._custom_offices_registry() is             agent._custom_offices_registry()
        assert agent._custom_offices_store is             agent._custom_offices_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.custom_offices_status()
        agent.custom_office_handoffs("gatekeeper")
        agent.custom_office_contract("gatekeeper", "auditor")
        assert agent._custom_offices_registry().list_definitions() == ()
        assert _custom_events(store, session_id) == []
        agent.close()

    def test_unheld_office_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_custom_office_definition("gatekeeper")

    def test_shipped_office_raises_valueerror(self, agent):
        with pytest.raises(ValueError):
            agent.get_custom_office_definition("auditor")
        with pytest.raises(ValueError):
            agent.find_custom_office_definition("polymath")
        with pytest.raises(ValueError):
            agent.find_custom_office_definition("primary")

    def test_status_after_register_shows_the_held_office(self, agent):
        agent.register_custom_office(_office())
        status = agent.custom_offices_status()
        assert [d["office"] for d in status["offices"]] == ["gatekeeper"]
        assert "Custom offices: 1 defined." in status["screen"]
        assert len(status["book"]) == 2


class TestCustomOfficesAgentRegister:
    def test_register_holds_and_publishes_once(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_custom_office(_office())
        assert outcome["office"]["office"] == "gatekeeper"
        assert outcome["record"]["type"] == "custom_office"
        assert outcome["record"]["news"] is True
        assert outcome["record"]["formal"] is False
        assert outcome["record"]["custom"] is True
        assert agent.get_custom_office_definition(
            "gatekeeper").title == "Gatekeeper"
        events = _custom_events(store, session_id)
        assert len(events) == 1
        assert events[0]["office"] == "gatekeeper"
        # Deduped per record id: a second publish is no second event.
        agent._publish_custom_office_record(outcome["record"])
        assert len(_custom_events(store, session_id)) == 1
        # Foreign record types are never published on this road.
        agent._publish_custom_office_record(
            {"type": "office", "office": "scribe"})
        agent._publish_custom_office_record(
            {"type": "crew_member", "office": "gatekeeper"})
        assert len(_custom_events(store, session_id)) == 1
        agent.close()

    def test_register_duplicate_refuses_and_holds_nothing_new(
            self, agent):
        agent.register_custom_office(_office())
        with pytest.raises(ValueError):
            agent.register_custom_office(_office())
        assert len(agent._custom_offices_registry().list_definitions()) == 1

    def test_register_formalised_office_refuses(self, agent):
        formal = build_office({
            "id": "auditor", "title": "Auditor", "focus": "verify",
            "purpose": get_office("auditor").purpose,
            "duties": ["Check."], "tools": ["read_file"],
            "inputs": ["a change"], "outputs": ["a verdict"],
            "handoffs": []})
        with pytest.raises(ValueError):
            agent.register_custom_office(formal)
        assert agent._custom_offices_registry().list_definitions() == ()

    def test_load_book_holds_and_publishes_the_examples(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.load_custom_offices_book()
        assert outcome["count"] == 2
        assert [d["office"] for d in outcome["offices"]] == list(
            EXAMPLE_CUSTOM_OFFICES)
        assert agent.get_custom_office_definition(
            "benchmarker").title == "Benchmarker"
        status = agent.custom_offices_status()
        assert len(status["offices"]) == 2
        assert "Custom offices: 2 defined." in status["screen"]
        events = _custom_events(store, session_id)
        assert len(events) == 2
        assert {e["office"] for e in events} == set(EXAMPLE_CUSTOM_OFFICES)
        with pytest.raises(ValueError):
            agent.load_custom_offices_book()
        agent.close()

    def test_book_from_a_file_is_held_at_the_agent_layer(
            self, agent, tmp_path):
        outcome = agent.load_custom_offices_book(
            load_custom_offices_file(_write_book(tmp_path, _book_data())))
        assert outcome["count"] == 2
        assert agent.get_custom_office_definition(
            "benchmarker").office == "benchmarker"

    def test_find_handoffs_and_contract_roads(self, agent):
        found = agent.find_custom_office_definition("Gatekeeper")
        assert found.office == "gatekeeper"
        contracts = agent.custom_office_handoffs("gatekeeper")
        assert [c.to_office for c in contracts] == [
            "auditor", "forge_worker"]
        contract = agent.custom_office_contract("benchmarker", "gatekeeper")
        assert contract.artifact
        formal = agent.custom_office_contract("gatekeeper", "auditor")
        assert formal.artifact
        with pytest.raises(KeyError):
            agent.custom_office_contract("gatekeeper", "benchmarker")
        # A held definition answers before the book does.
        agent.register_custom_office(_office())
        assert agent.find_custom_office_definition(
            "gatekeeper").duties[0] == "Review the change."
        assert [c.to_office for c in agent.custom_office_handoffs(
            "gatekeeper")] == ["auditor"]

    def test_no_spawn_road_for_custom_offices(self, agent):
        # A custom office is a user-defined role, not a
        # formalised office and not a cast member:
        # spawning stays the M-121 crew road, and this
        # layer builds no spawn road of its own.
        assert not hasattr(agent, "spawn_custom_office")
        assert not hasattr(agent, "spawn_custom_offices")


class TestCustomOfficesTerminalSurface:
    def test_show_one_handoffs_and_contract(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/offices custom")
        assert "Custom offices: 2 defined." in text
        _, _, text = _slash(agent, "/offices custom show gatekeeper")
        assert "gatekeeper:" in text
        _, _, text = _slash(agent, "/offices custom handoffs gatekeeper")
        assert "-> auditor" in text and "-> forge_worker" in text
        _, _, text = _slash(
            agent, "/offices custom contract gatekeeper auditor")
        assert "gatekeeper -> auditor" in text
        _, _, text = _slash(
            agent, "/offices custom contract gatekeeper benchmarker")
        assert "no hand-off" in text

    def test_formal_offices_road_is_untouched(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/offices")
        assert "Offices: 6 formalised." in text
        _, _, text = _slash(agent, "/offices show auditor")
        assert "auditor:" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/offices custom [show|show <office>|handoffs <office>|"
                "contract <from> <to>]") in text
        _, _, text = _slash(agent, "/offices custom add x")
        assert text == USAGE
        _, _, text = _slash(agent, "/offices custom show auditor")
        assert text == USAGE

    def test_bare_custom_id_shows_one(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/offices custom benchmarker")
        assert "benchmarker:" in text


@pytest.fixture()
def custom_offices_handler(agent, monkeypatch):
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


def _custom_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCustomOfficesCommand:
    def test_show_is_default(self, custom_offices_handler, agent):
        custom_offices_handler._handle_offices("custom")
        assert "Custom offices: 2 defined." in _custom_published_text(
            custom_offices_handler)

    def test_show_one_handoffs_and_contract(
            self, custom_offices_handler, agent):
        custom_offices_handler._handle_offices("custom show gatekeeper")
        assert "gatekeeper:" in _custom_published_text(custom_offices_handler)
        custom_offices_handler._handle_offices("custom handoffs benchmarker")
        assert "-> gatekeeper" in _custom_published_text(custom_offices_handler)
        custom_offices_handler._handle_offices(
            "custom contract benchmarker gatekeeper")
        assert "benchmarker -> gatekeeper" in _custom_published_text(
            custom_offices_handler)

    def test_bad_grammar_is_published(self, custom_offices_handler, agent):
        custom_offices_handler._handle_offices("custom add x")
        assert "Usage: /offices custom" in _custom_published_text(
            custom_offices_handler)

    def test_missing_contract_is_published(
            self, custom_offices_handler, agent):
        custom_offices_handler._handle_offices(
            "custom contract gatekeeper benchmarker")
        assert "no hand-off" in _custom_published_text(custom_offices_handler)

    def test_formal_road_still_shows_the_six(
            self, custom_offices_handler, agent):
        custom_offices_handler._handle_offices("")
        assert "Offices: 6 formalised." in _custom_published_text(
            custom_offices_handler)


class TestChatScreenRoutingCustomOffices:
    def test_custom_offices_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/offices custom handoffs gatekeeper", _FakeLog())
        assert calls == [("/offices", "custom handoffs gatekeeper")]
