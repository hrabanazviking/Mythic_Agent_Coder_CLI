"""M-143 Crew templates - pure-layer tests.

TIER: integration

The pure layer is the saved formations as data: a
crew template book of formation records (one saved
formation, named in plain words, fielding seats
that each name a member of the shipped casting),
the shipped example template book held in a data
file, a loader that reads a template book from any
file, per-formation rosters whose member list, size
and account are derived from the formation's seats,
the template index whose rows, totals and account
are derived from the whole book, records shaped as
session news, and a registry. Nothing here summons
a crew, spawns an agent, calls a model or persists
anything: a stored roster disagreeing with the
roster derived from its own formation is refused,
and a stored index disagreeing with the index
derived from its book is refused. Size is derived
from the held seats, never stored loose: a stored
size key on a record refuses as an unknown key.
Summonable by name here means a name resolves to
the validated formation record, nothing more.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.validation import ValidationError
from mythic_agent.core.crew_templates import (
    PLAIN_EXPLANATION,
    CREW_TEMPLATES_RESOURCE,
    CREW_TEMPLATES_SCHEMA,
    CREW_TEMPLATES_SLICE,
    USAGE,
    CrewTemplate,
    CrewTemplateBook,
    FormationRoster,
    TemplateIndex,
    TemplateRegistry,
    book_record,
    build_book,
    build_index,
    build_roster,
    build_template,
    derive_index,
    derive_roster,
    format_crew_templates_screen,
    format_index,
    format_roster,
    format_template,
    format_templates,
    index_plain_words,
    index_record,
    load_crew_templates,
    load_crew_templates_file,
    parse_crew_templates_args,
    plain_words,
    roster_plain_words,
    roster_record,
    template_record,
    validate_book,
    validate_index,
    validate_roster,
    validate_template,
)

ROOT = Path(__file__).resolve().parents[1]


def _tpl(**kwargs):
    kwargs.setdefault("template_id", "tpl-duo")
    kwargs.setdefault("template", "duo")
    kwargs.setdefault("title", "Duo")
    kwargs.setdefault(
        "detail", "One pair of hands plus the eyes that check them.")
    kwargs.setdefault("slots", ["forge_worker", "auditor"])
    return CrewTemplate(**kwargs)


def _tpls():
    return [
        _tpl(),
        CrewTemplate(
            template_id="tpl-full-six", template="full_six",
            title="Full Six",
            detail="The six offices standing together.",
            slots=["skald", "architect", "forge_worker",
                   "auditor", "cartographer", "scribe"]),
        CrewTemplate(
            template_id="tpl-research-swarm",
            template="research_swarm", title="Research Swarm",
            detail="The Cartographer-led fan-out.",
            slots=["cartographer", "architect", "skald", "scribe"],
            lead="cartographer"),
        CrewTemplate(
            template_id="tpl-review-panel",
            template="review_panel", title="Review Panel",
            detail="Two checking members, one change.",
            slots=["auditor", "guardian"]),
    ]


def test_constants_and_usage():
    assert CREW_TEMPLATES_SLICE == "M-143"
    assert CREW_TEMPLATES_SCHEMA == "mythic.crew_templates/1"
    assert CREW_TEMPLATES_RESOURCE == "crew_templates.yaml"
    assert "summonable by name" in PLAIN_EXPLANATION
    assert "data only" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /templates")
    assert "/templates template <template>" in USAGE
    assert "/templates index" in USAGE


def test_shipped_example_shape():
    book = load_crew_templates()
    assert book.title == "Crew template book at the M-142 slice boundary"
    assert book.template_ids() == (
        "tpl-duo", "tpl-full-six",
        "tpl-research-swarm", "tpl-review-panel")
    assert book.template_words() == (
        "duo", "full_six", "research_swarm", "review_panel")
    assert tuple(e.size for e in book.entries) == (2, 6, 4, 2)
    swarm = book.template_named("research_swarm")
    assert swarm.lead == "cartographer"
    assert swarm.members == (
        "cartographer", "architect", "skald", "scribe")
    panel = book.resolve_template("tpl-review-panel")
    assert panel.template == "review_panel"
    assert book.resolve_template("duo").template_id == "tpl-duo"


def test_shipped_index():
    book = load_crew_templates()
    index = book.index_for("index-m142-boundary")
    assert tuple(r.template for r in index.rows) == (
        "duo", "full_six", "research_swarm", "review_panel")
    assert (index.total_templates, index.total_slots,
            index.total_members) == (4, 14, 7)
    derived = derive_index(book.entries)
    assert derived.rows == index.rows
    assert derived.account == index.account


def test_record_validation_and_aliases():
    record = validate_template({
        "id": "tpl-duo", "name": "duo", "headline": "Duo",
        "purpose": "One pair of hands plus checking eyes.",
        "seats": ["forge_worker", "auditor"]})
    assert record.template_id == "tpl-duo"
    assert record.template == "duo"
    assert record.title == "Duo"
    assert record.slots == ("forge_worker", "auditor")
    assert record.members == ("forge_worker", "auditor")
    assert record.size == 2
    assert record.lead is None


def test_two_spellings_refusals():
    with pytest.raises(ValueError):
        validate_template({
            "template": "duo", "name": "pair", "title": "Duo",
            "detail": "Two members.", "slots": ["auditor"]})
    with pytest.raises(ValueError):
        validate_template({
            "template": "duo", "title": "Duo",
            "detail": "Two members.",
            "slots": ["auditor"], "seats": ["scribe"]})
    with pytest.raises(ValueError):
        validate_roster({
            "template": "duo", "members": ["auditor"],
            "member_ids": ["scribe"], "size": 1,
            "account": ["One member."]})


def test_unknown_key_refusals():
    with pytest.raises(ValueError):
        validate_template({
            "template": "duo", "title": "Duo",
            "detail": "Two members.", "slots": ["auditor"],
            "size": 1})
    with pytest.raises(ValueError):
        validate_template({
            "template": "duo", "title": "Duo",
            "detail": "Two members.", "slots": ["auditor"],
            "members": ["auditor"]})
    with pytest.raises(ValueError):
        validate_template({
            "template": "duo", "title": "Duo",
            "detail": "Two members.", "slots": ["auditor"],
            "count": 1})


def test_lead_must_hold_a_seat():
    record = _tpls()[2]
    assert record.lead == "cartographer"
    assert record.lead in record.slots
    with pytest.raises(ValueError):
        CrewTemplate(
            template="research_swarm", title="Research Swarm",
            detail="A fan-out.", slots=["architect", "skald"],
            lead="cartographer")
    with pytest.raises(ValueError):
        _tpl(slots=["auditor", "auditor"])


def test_malformed_records():
    with pytest.raises(ValueError):
        _tpl(template="not a word!")
    with pytest.raises(ValueError):
        _tpl(title="")
    with pytest.raises(ValueError):
        validate_template({
            "template": "duo", "title": "Duo",
            "slots": ["auditor"]})
    with pytest.raises(ValueError):
        _tpl(slots=[])


def test_roster_derivation():
    roster = derive_roster(_tpl())
    assert roster.template == "duo"
    assert roster.members == ("forge_worker", "auditor")
    assert roster.size == 2
    assert roster.template_id == "tpl-duo"
    assert roster.account[0] == (
        "duo fields 2 member(s): forge_worker, auditor.")


def _roster_mapping(roster):
    return {
        "roster_id": roster.roster_id,
        "template_id": roster.template_id,
        "template": roster.template,
        "members": list(roster.members),
        "size": roster.size,
        "account": list(roster.account)}


def test_stored_roster_judged():
    roster = derive_roster(_tpl())
    stored = _roster_mapping(roster)
    assert validate_roster(stored, _tpl()) == roster
    assert validate_roster(stored, _tpl()).members == roster.members
    bad = dict(stored, size=3)
    with pytest.raises(ValueError):
        validate_roster(bad, _tpl())
    bad_account = dict(
        stored, account=["A different account altogether."])
    with pytest.raises(ValueError):
        validate_roster(bad_account, _tpl())


def test_accountless_roster_refusal():
    with pytest.raises(ValueError):
        validate_roster({
            "template": "duo", "members": ["auditor"], "size": 1})


def test_index_derivation():
    index = derive_index(_tpls())
    assert index.total_templates == 4
    assert index.total_slots == 14
    assert index.total_members == 7
    assert index.row_for("full_six").size == 6
    with pytest.raises(KeyError):
        index.row_for("nobody")
    with pytest.raises(ValueError):
        derive_index([])


def test_stored_index_judged():
    index = derive_index(_tpls())
    stored = {
        "index_id": index.index_id,
        "rows": [_roster_mapping(r) for r in index.rows],
        "total_templates": index.total_templates,
        "total_slots": index.total_slots,
        "total_members": index.total_members,
        "account": list(index.account)}
    assert validate_index(stored, _tpls()).rows == index.rows
    bad = dict(stored, total_slots=99)
    with pytest.raises(ValueError):
        validate_index(bad, _tpls())
    with pytest.raises(ValueError):
        TemplateIndex(
            rows=index.rows, total_templates=4, total_slots=13,
            total_members=7, account=index.account)


def test_duplicate_refusals():
    with pytest.raises(ValueError):
        CrewTemplateBook(
            title="A book", entries=[_tpl(), _tpl()])
    with pytest.raises(ValueError):
        CrewTemplateBook(
            title="A book",
            entries=[_tpl(), _tpl(template_id="tpl-other")])
    with pytest.raises(ValueError):
        CrewTemplateBook(
            title="A book",
            entries=[_tpl(), _tpl(template="pair")])


def test_book_index_disagreement_refuses():
    book = load_crew_templates()
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "crew_templates.yaml").read_text())
    raw["indexes"][0]["total_slots"] = 99
    raw["indexes"][0]["rows"][0]["size"] = 5
    raw["indexes"][0]["rows"][0]["members"] = [
        "forge_worker", "auditor", "scribe", "skald", "guardian"]
    with pytest.raises(ValidationError):
        validate_book(raw)


def test_file_loader_round_trip_and_missing(tmp_path):
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "crew_templates.yaml").read_text())
    path = tmp_path / "templates.yaml"
    path.write_text(yaml.safe_dump(raw))
    book = load_crew_templates_file(path)
    assert book.template_words() == (
        "duo", "full_six", "research_swarm", "review_panel")
    with pytest.raises(FileNotFoundError):
        load_crew_templates_file(tmp_path / "nope.yaml")


def test_registry_auto_ids_and_duplicates():
    registry = TemplateRegistry()
    first = registry.register_template({
        "template": "duo", "title": "Duo",
        "detail": "Two members.", "slots": ["forge_worker", "auditor"]})
    assert first.template_id == "template-1"
    second = registry.register_template({
        "template": "pair_plus", "title": "Pair Plus",
        "detail": "Three members.",
        "slots": ["forge_worker", "auditor", "scribe"]})
    assert second.template_id == "template-2"
    with pytest.raises(ValueError):
        registry.register_template({
            "template": "duo", "title": "Duo Again",
            "detail": "The same name twice.",
            "slots": ["auditor"]})
    assert registry.resolve_template("duo").template_id == "template-1"
    assert registry.roster_for("duo").size == 2
    assert registry.index().total_templates == 2


def test_registry_book_title_clash():
    registry = TemplateRegistry()
    registry.register_book(load_crew_templates())
    other = CrewTemplateBook(
        title="Another book entirely",
        entries=[CrewTemplate(
            template_id="tpl-solo-plus", template="solo_plus",
            title="Solo Plus", detail="One member and a checker.",
            slots=["polymath", "auditor"])])
    with pytest.raises(ValueError):
        registry.register_book(other)
    assert registry.book().title == (
        "Crew template book at the M-142 slice boundary")


def test_session_news_records():
    record = template_record(_tpl())
    assert record["type"] == "crew_template"
    assert record["slice"] == "M-143"
    assert record["news"] is True
    assert "summonable by name" in record["headline"]
    assert record["size"] == 2
    roster = roster_record(derive_roster(_tpl()), _tpl())
    assert roster["type"] == "crew_formation_roster"
    assert roster["slice"] == "M-143"
    assert roster["news"] is True
    index = index_record(derive_index(_tpls()), _tpls())
    assert index["type"] == "crew_template_index"
    assert index["news"] is True
    book = book_record(load_crew_templates())
    assert book["type"] == "crew_template_book"
    assert book["template_count"] == 4


def test_plain_words():
    text = plain_words(_tpls()[2])
    assert text.startswith("research_swarm - Research Swarm:")
    assert "cartographer leads it" in text
    assert "4 member(s)" in text
    roster_text = roster_plain_words(load_crew_templates())
    assert "duo - 2 member(s)" in roster_text
    index_text = index_plain_words(load_crew_templates())
    assert "Template index:" in index_text
    assert "14 seat(s)" in index_text


def test_formatters_and_screen():
    line = format_template(_tpl())
    assert line.startswith("tpl-duo: duo - Duo")
    assert "2 member(s): forge_worker, auditor" in line
    book = load_crew_templates()
    all_lines = format_templates(book)
    assert "tpl-full-six" in all_lines
    filtered = format_templates(book, member="guardian")
    assert "review_panel" in filtered
    assert "full_six" not in filtered
    roster_text = format_roster(book)
    assert "Rosters in Crew template book" in roster_text
    index_text = format_index(book)
    assert "Template index:" in index_text
    screen = format_crew_templates_screen()
    assert "Crew templates (M-143)" in screen
    assert USAGE in screen


def test_parser_grammar():
    assert parse_crew_templates_args("") == ("show", None)
    assert parse_crew_templates_args("show") == ("show", None)
    assert parse_crew_templates_args("list") == ("show", None)
    assert parse_crew_templates_args("template duo") == (
        "template", "duo")
    assert parse_crew_templates_args("member auditor") == (
        "member", "auditor")
    assert parse_crew_templates_args("roster full_six") == (
        "roster", "full_six")
    assert parse_crew_templates_args("index") == ("index", None)
    with pytest.raises(ValueError):
        parse_crew_templates_args("summon duo")
    with pytest.raises(ValueError):
        parse_crew_templates_args("template")
    with pytest.raises(ValueError):
        parse_crew_templates_args("index now")


def test_builders_from_field_words():
    record = build_template({
        "template": "duo", "title": "Duo", "detail": "Two members.",
        "slots": ["forge_worker", "auditor"]})
    assert record.size == 2
    roster = build_roster(
        template="duo", members=["forge_worker", "auditor"],
        size=2, account=["duo fields 2 member(s): "
                          "forge_worker, auditor."])
    assert roster.template == "duo"
    index = build_index(
        rows=[derive_roster(record)], total_templates=1,
        total_slots=2, total_members=2,
        account=["The book holds 1 saved formation(s)."])
    assert index.total_templates == 1
    book = build_book(
        title="A small book", entries=[record])
    assert isinstance(book, CrewTemplateBook)
    assert book.resolve_template("duo") is record
