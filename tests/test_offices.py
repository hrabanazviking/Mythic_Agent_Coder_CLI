"""M-122 The six offices formalised - pure-layer tests.

TIER: integration

The pure layer is the six offices as data: an
office definition (duties, tools, inputs, outputs,
hand-off contracts) validated as data, the shipped
book (the six offices the roadmap names, each a
shipped role-routing office, its tools exactly the
M-121 casting's tools for that office) held in a
data file, a loader that reads a book from any
file, hand-off contracts validated as a closed
graph, an office record shaped as session news,
and a registry. Nothing here spawns an agent or
runs a model.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting, member_offices
from mythic_agent.core.offices import (
    FORMAL_OFFICES,
    OFFICES_RESOURCE,
    OFFICES_SCHEMA,
    OFFICES_SLICE,
    PLAIN_EXPLANATION,
    UNFORMALISED_OFFICES,
    USAGE,
    HandoffContract,
    OfficeDefinition,
    OfficeRegistry,
    OfficesBook,
    build_office,
    formal_office_ids,
    format_office,
    format_offices,
    format_offices_screen,
    load_offices,
    load_offices_file,
    normalize_formal_office,
    office_record,
    parse_offices_args,
    plain_words,
    validate_office,
    validate_offices,
)
from mythic_agent.core.role_routing import get_office, office_ids
from mythic_agent.core.tool_schemas import get_agent_tools
from mythic_agent.core.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def _office(**kwargs):
    kwargs.setdefault("office", "auditor")
    kwargs.setdefault("title", "Auditor")
    kwargs.setdefault("focus", "verify")
    kwargs.setdefault("purpose", get_office("auditor").purpose)
    kwargs.setdefault("duties", ["Check built work.", "Give a plain verdict."])
    kwargs.setdefault("tools", ["read_file", "run_command"])
    kwargs.setdefault("inputs", ["a built change"])
    kwargs.setdefault("outputs", ["a verification verdict"])
    kwargs.setdefault("handoffs", [{
        "to": "scribe", "artifact": "the verdict",
        "condition": "the verdict is recorded"}])
    return OfficeDefinition(**kwargs)


def _book_data():
    return {
        "schema": OFFICES_SCHEMA, "slice": OFFICES_SLICE,
        "offices": [
            {"id": "auditor", "title": "Auditor", "focus": "verify",
             "purpose": get_office("auditor").purpose,
             "duties": ["Check built work."], "tools": ["read_file"],
             "inputs": ["a built change"], "outputs": ["a verdict"],
             "handoffs": [{"to": "scribe", "artifact": "the verdict",
                           "condition": "it is recorded"}]},
            {"id": "scribe", "title": "Scribe", "focus": "memory & docs",
             "purpose": get_office("scribe").purpose,
             "duties": ["Write the record."], "tools": ["write_file"],
             "inputs": ["a verdict"], "outputs": ["a written record"],
             "handoffs": []},
        ]}


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert OFFICES_SLICE == "M-122"
    assert OFFICES_SCHEMA == "mythic.offices/1"
    assert OFFICES_RESOURCE == "offices.yaml"
    assert USAGE.startswith("Usage: /offices")
    assert "handoffs" in USAGE and "contract" in USAGE
    assert "six offices" in PLAIN_EXPLANATION
    assert "polymath and guardian" in PLAIN_EXPLANATION


def test_formal_offices_are_the_roadmaps_six_from_the_shipped_vocabulary():
    assert formal_office_ids() == (
        "skald", "architect", "forge_worker",
        "auditor", "cartographer", "scribe")
    assert FORMAL_OFFICES == formal_office_ids()
    for office in FORMAL_OFFICES:
        assert office in office_ids()
        assert office in member_offices()
    assert "primary" not in FORMAL_OFFICES


def test_unformalised_offices_are_named_honestly():
    assert UNFORMALISED_OFFICES == ("polymath", "guardian")
    assert set(UNFORMALISED_OFFICES) | set(FORMAL_OFFICES) == set(member_offices())
    assert "primary" not in UNFORMALISED_OFFICES


def test_word_readings():
    assert normalize_formal_office("Forge-Worker") == "forge_worker"
    assert normalize_formal_office(" ARCHITECT ") == "architect"
    assert normalize_formal_office("skald") == "skald"
    for bad in ("polymath", "guardian", "primary", "Primary",
                "captain", "", None, 4):
        with pytest.raises(ValueError):
            normalize_formal_office(bad)


# -- the shipped book: the six offices, formalised ----------------------------


def test_shipped_book_loads_and_is_complete():
    book = load_offices()
    assert isinstance(book, OfficesBook)
    assert [d.office for d in book.definitions] == list(FORMAL_OFFICES)
    assert book.formal_note
    assert "polymath" in book.formal_note and "guardian" in book.formal_note
    rebuilt = {"schema": OFFICES_SCHEMA, "slice": OFFICES_SLICE,
               "offices": [{
                   "id": d.office, "title": d.title, "focus": d.focus,
                   "purpose": d.purpose, "duties": list(d.duties),
                   "tools": list(d.tools), "inputs": list(d.inputs),
                   "outputs": list(d.outputs),
                   "handoffs": [c.to_record() for c in d.handoffs]}
                   for d in book.definitions]}
    assert validate_offices(rebuilt, require_complete=True) == []


def test_titles_purposes_and_focus_are_the_shipped_and_roadmap_words():
    book = load_offices()
    focuses = {"skald": "intent & vision", "architect": "design",
               "forge_worker": "build", "auditor": "verify",
               "cartographer": "map & research", "scribe": "memory & docs"}
    for definition in book.definitions:
        shipped = get_office(definition.office)
        assert definition.title == shipped.title
        assert definition.purpose == shipped.purpose
        assert definition.focus == focuses[definition.office]


def test_tools_are_exactly_the_m121_casting_tools():
    book = load_offices()
    casting = load_casting()
    shipped_tools = {t["function"]["name"] for t in get_agent_tools()}
    for definition in book.definitions:
        member = casting.by_office(definition.office)
        assert definition.tools == member.tools
        for tool in definition.tools:
            assert tool in shipped_tools


def test_every_office_carries_duties_inputs_and_outputs():
    book = load_offices()
    for definition in book.definitions:
        assert len(definition.duties) >= 3
        assert definition.inputs and definition.outputs


def test_handoff_graph_is_closed_and_complete():
    book = load_offices()
    pairs = {(d.office, c.to_office)
             for d in book.definitions for c in d.handoffs}
    assert pairs == {
        ("skald", "architect"), ("skald", "cartographer"),
        ("architect", "forge_worker"), ("architect", "cartographer"),
        ("forge_worker", "auditor"), ("forge_worker", "scribe"),
        ("auditor", "forge_worker"), ("auditor", "scribe"),
        ("cartographer", "architect"), ("cartographer", "forge_worker"),
        ("scribe", "skald")}
    assert len(pairs) == 11
    for definition in book.definitions:
        assert definition.handoffs
        for contract in definition.handoffs:
            assert contract.artifact and contract.condition
    assert book.contract("auditor", "forge_worker").artifact
    assert book.handoffs_to("scribe")
    with pytest.raises(KeyError):
        book.contract("scribe", "auditor")
    with pytest.raises(KeyError):
        book.contract("skald", "scribe")
    with pytest.raises(ValueError):
        book.get("polymath")


# -- definition construction and refusals -------------------------------------


def test_definition_construction_and_record():
    office = _office()
    record = office.to_record()
    assert record["type"] == "office" and record["slice"] == "M-122"
    assert record["office"] == "auditor"
    assert record["handoffs"][0]["to"] == "scribe"
    assert office.contract_to("scribe").artifact == "the verdict"
    with pytest.raises(KeyError):
        office.contract_to("skald")
    contract = HandoffContract(to_office="Forge-Worker", artifact="a",
                               condition="b")
    assert contract.to_office == "forge_worker"


def test_definition_refusals():
    with pytest.raises(ValueError):
        _office(office="polymath")
    with pytest.raises(ValueError):
        _office(office="captain")
    with pytest.raises(ValueError):
        _office(title=" ")
    with pytest.raises(ValueError):
        _office(duties=[])
    with pytest.raises(ValueError):
        _office(duties=["Check.", "Check."])
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
        _office(handoffs=[{"to": "auditor", "artifact": "x",
                           "condition": "y"}])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "scribe", "artifact": "x",
                           "condition": "y"},
                          {"to": "scribe", "artifact": "z",
                           "condition": "w"}])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "polymath", "artifact": "x",
                           "condition": "y"}])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "scribe", "artifact": "x"}])
    with pytest.raises(ValueError):
        _office(handoffs=[{"to": "scribe", "artifact": "x",
                           "condition": "y", "speed": "fast"}])


def test_mapping_aliases_and_two_spellings_refusal():
    data = {"id": "auditor", "title": "Auditor", "focus": "verify",
            "purpose": get_office("auditor").purpose,
            "duties": ["Check."], "tools": ["read_file"],
            "inputs": ["a change"], "outputs": ["a verdict"],
            "handoffs": []}
    assert validate_office(data).office == "auditor"
    assert build_office(data).office == "auditor"
    both_same = dict(data, office="auditor")
    assert validate_office(both_same).office == "auditor"
    with pytest.raises(ValueError):
        validate_office(dict(data, office="scribe"))
    with pytest.raises(ValueError):
        validate_office(dict(data, rank="first"))
    with pytest.raises(ValueError):
        validate_office({k: v for k, v in data.items() if k != "duties"})
    with pytest.raises(ValueError):
        validate_office("auditor")
    built = build_office(office="scribe", title="Scribe",
                         focus="memory & docs",
                         purpose=get_office("scribe").purpose,
                         duties=["Write."], tools=["write_file"],
                         inputs=["a summary"], outputs=["a record"],
                         handoffs=[])
    assert built.office == "scribe"


# -- book validation and file loading ------------------------------------------


def test_book_refusals():
    good = _book_data()
    assert validate_offices(good) == []
    assert validate_offices("nope") != []
    assert validate_offices(dict(good, schema="mythic.other/9")) != []
    assert validate_offices(dict(good, slice="M-999")) != []
    assert validate_offices(dict(good, offices=[])) != []
    assert validate_offices(dict(good, extra=1)) != []
    doubled = _book_data()
    doubled["offices"] = doubled["offices"] + [doubled["offices"][0]]
    assert any("duplicate" in p for p in validate_offices(doubled))
    dangling = _book_data()
    dangling["offices"] = dangling["offices"][:1]
    assert any("does not define" in p for p in validate_offices(dangling))
    incomplete = validate_offices(good, require_complete=True)
    assert any("skald" in p for p in incomplete)
    wrong_title = _book_data()
    wrong_title["offices"][0]["title"] = "Checker"
    problems = validate_offices(wrong_title, require_complete=True)
    assert any("title" in p for p in problems)
    with pytest.raises(ValidationError):
        load_offices(dict(good, schema="mythic.other/9"))


def _write_book(tmp_path, data):
    path = tmp_path / "offices.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_load_offices_file_roundtrip(tmp_path):
    book = load_offices_file(_write_book(tmp_path, _book_data()))
    assert [d.office for d in book.definitions] == ["auditor", "scribe"]
    assert book.contract("auditor", "scribe").condition == "it is recorded"


def test_load_offices_file_single_office(tmp_path):
    data = _book_data()
    data["offices"] = [dict(data["offices"][1])]
    book = load_offices_file(_write_book(tmp_path, data))
    assert [d.office for d in book.definitions] == ["scribe"]


def test_load_offices_file_refusals(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_offices_file(tmp_path / "missing.yaml")
    bad = _write_book(tmp_path, {"schema": "x", "offices": "nope"})
    with pytest.raises(ValidationError):
        load_offices_file(bad)
    malformed = tmp_path / "broken.yaml"
    malformed.write_text("offices: [unclosed\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_offices_file(malformed)
    unknown_office = _book_data()
    unknown_office["offices"][0]["id"] = "polymath"
    with pytest.raises(ValidationError):
        load_offices_file(_write_book(tmp_path, unknown_office))


# -- registry, news record, plain words, formatters, parser -------------------


def test_registry_holds_the_book_and_refuses_duplicates():
    registry = OfficeRegistry()
    held = registry.register_book(load_offices())
    assert [d.office for d in held] == list(FORMAL_OFFICES)
    assert registry.get("Forge-Worker").office == "forge_worker"
    assert registry.list_definitions() == held
    with pytest.raises(ValueError):
        registry.register(held[0])
    with pytest.raises(KeyError):
        OfficeRegistry().get("skald")
    with pytest.raises(ValueError):
        registry.register_book("not a book")


def test_office_record_is_session_news():
    record = office_record(load_offices().get("skald"))
    assert record["news"] is True
    assert record["type"] == "office" and record["slice"] == "M-122"
    assert record["office"] == "skald"
    assert "Skald" in record["headline"]


def test_plain_words_and_formatters():
    book = load_offices()
    words = plain_words(book.get("forge_worker"))
    assert "Forge Worker" in words and "build" in words
    assert "auditor" in words
    assert format_office(book.get("scribe")).startswith("  scribe:")
    text = format_offices(book)
    assert text.startswith("Offices: 6 formalised.")
    assert format_offices() == "Offices: none. No offices are formalised."
    assert format_offices(OfficeRegistry()) == (
        "Offices: none. No offices are formalised.")
    screen = format_offices_screen(book)
    assert "M-122" in screen and USAGE in screen
    with pytest.raises(ValueError):
        format_offices("skald")


def test_parser():
    assert parse_offices_args("") == ("show", None)
    assert parse_offices_args(None) == ("show", None)
    assert parse_offices_args("show") == ("show", None)
    assert parse_offices_args("list") == ("show", None)
    assert parse_offices_args("show Forge-Worker") == ("show", "forge_worker")
    assert parse_offices_args("skald") == ("show", "skald")
    assert parse_offices_args("handoffs auditor") == ("handoffs", "auditor")
    assert parse_offices_args("contract auditor scribe") == (
        "contract", ("auditor", "scribe"))
    for bad in ("show polymath", "handoffs", "contract auditor",
                "contract auditor polymath", "show a b", "dance", 4):
        with pytest.raises(ValueError):
            parse_offices_args(bad)


def test_module_purity():
    source = (ROOT / "mythic_agent" / "core" / "offices.py").read_text(
        encoding="utf-8")
    for banned in ("agents.llm", "terminal", "command_handler", "import os"):
        assert banned not in source
