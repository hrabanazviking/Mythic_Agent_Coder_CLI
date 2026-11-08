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


# -- agent layer -----------------------------------------------------------
#
# M-143 agent layer: the agent holds a
# TemplateRegistry for the session (session state
# only, no new setting), template records are held
# by being registered - published as their
# template_record session news with their derived
# roster_record, and a whole book's derived
# index_record, through the checkpoint road, deduped
# per id - the report road renders the held book (or
# the shipped example when unheld) through the pure
# formatters, and the /templates surface rides both
# roads on the pure parser + formatters. Status, get,
# roster and index reads register and publish
# nothing, answer from the held registry first and
# from the shipped example only while nothing is
# held - a held session never falls back to the
# example. Rosters and the index derive at call time
# from the held records, never held. This layer
# summons no crew, spawns no agent, runs no agent,
# calls no model and persists nothing - and there is
# no Part VIII board yet, so the screen is where the
# crew templates are visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _template_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_template_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "crew_templates.yaml").read_text(encoding="utf-8")
    path = tmp_path / "crew_templates.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCrewTemplatesAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.crew_templates_status()
        assert status["templates"] == []
        assert status["book"] is None
        assert status["crew_templates"]["title"] == (
            "Crew template book at the M-142 slice boundary")
        assert [t["template_id"]
                for t in status["crew_templates"]["templates"]] == [
            "tpl-duo", "tpl-full-six",
            "tpl-research-swarm", "tpl-review-panel"]
        assert status["book_record"]["type"] == "crew_template_book"
        assert status["book_record"]["template_count"] == 4
        assert status["book_record"]["index_count"] == 1
        assert [r["template"] for r in status["rosters"]] == [
            "duo", "full_six", "research_swarm", "review_panel"]
        assert [r["size"] for r in status["rosters"]] == [2, 6, 4, 2]
        assert [i["index_id"] for i in status["indexes"]] == [
            "index-m142-boundary"]
        assert status["index"]["total_templates"] == 4
        assert status["index"]["total_slots"] == 14
        assert status["index"]["total_members"] == 7
        assert "duo -" in status["plain_words"][0]
        assert "duo - 2 member(s)" in status["roster_plain_words"]
        assert "Template index:" in status["index_plain_words"]
        assert "Crew templates (M-143)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._crew_templates_registry() is \
            agent._crew_templates_registry()
        assert agent._crew_templates_store is \
            agent._crew_templates_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.crew_templates_status()
        template = agent.get_crew_template("duo")
        assert template.template_id == "tpl-duo"
        assert agent.get_crew_template("tpl-full-six").template == "full_six"
        roster = agent.crew_template_roster("research_swarm")
        assert roster.size == 4
        assert roster.members[0] == "cartographer"
        index = agent.crew_template_index()
        assert index.total_templates == 4
        assert index.total_slots == 14
        assert agent.crew_templates().title == (
            "Crew template book at the M-142 slice boundary")
        registry = agent._crew_templates_registry()
        assert registry.list_templates() == ()
        for kind in ("crew_template", "crew_formation_roster",
                     "crew_template_index"):
            assert _template_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_crew_template("no-such-formation")
        with pytest.raises(KeyError):
            agent.crew_template_roster("no-such-formation")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_crew_template(_tpl())
        status = agent.crew_templates_status()
        assert [t["template_id"] for t in status["templates"]] == ["tpl-duo"]
        assert status["book"]["template_count"] == 1
        # The held book answers now, not the example:
        # records held one by one stand under a session
        # crew template book, and it holds no indexes -
        # the index stays a derivation.
        assert status["crew_templates"]["title"] == (
            "Session crew template book")
        assert status["indexes"] == []
        assert status["index"]["total_templates"] == 1
        assert status["index"]["total_slots"] == 2
        assert status["index"]["total_members"] == 2
        assert "tpl-duo" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_crew_template(_tpl())
        with pytest.raises(KeyError):
            agent.get_crew_template("tpl-full-six")
        with pytest.raises(KeyError):
            agent.crew_template_roster("full_six")
        assert agent.crew_templates().template_ids() == ("tpl-duo",)
        assert agent.get_crew_template("duo").template_id == "tpl-duo"
        roster = agent.crew_template_roster("tpl-duo")
        assert roster.size == 2
        assert agent.crew_template_index().total_templates == 1


class TestCrewTemplatesAgentRegister:
    def test_register_template_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_crew_template(_tpl())
        assert outcome["template"]["template_id"] == "tpl-duo"
        assert outcome["record"]["type"] == "crew_template"
        assert outcome["roster_record"]["type"] == "crew_formation_roster"
        events = _template_events(store, session_id, "crew_template")
        assert len(events) == 1
        assert events[0]["template_id"] == "tpl-duo"
        rosters = _template_events(
            store, session_id, "crew_formation_roster")
        assert len(rosters) == 1
        assert rosters[0]["template"] == "duo"
        # The same records are never published twice.
        agent._publish_crew_templates_record(outcome["record"])
        agent._publish_crew_templates_record(outcome["roster_record"])
        assert len(_template_events(store, session_id, "crew_template")) == 1
        assert len(_template_events(
            store, session_id, "crew_formation_roster")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.dogfood import (
            entry_record as _dogfood_entry_record,
            load_dogfood,
        )
        from mythic_agent.core.solo_mode import (
            capability_record as _solo_capability_record,
            load_solo_mode,
        )
        agent._publish_crew_templates_record(book_record(
            load_crew_templates()))
        agent._publish_crew_templates_record(_solo_capability_record(
            load_solo_mode().entries[0]))
        agent._publish_crew_templates_record(_dogfood_entry_record(
            load_dogfood().entries[0]))
        for kind in ("crew_template_book", "solo_capability",
                     "dogfood_entry"):
            assert _template_events(store, session_id, kind) == []
        assert len(_template_events(store, session_id, "crew_template")) == 1
        agent.close()

    def test_duplicate_template_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_crew_template(_tpl())
        with pytest.raises(ValueError):
            agent.register_crew_template(_tpl())
        assert len(_template_events(store, session_id, "crew_template")) == 1
        agent.close()

    def test_register_template_without_id_gets_a_template_id(self, agent):
        outcome = agent.register_crew_template({
            "template": "duo", "title": "Duo",
            "detail": "One pair of hands plus the eyes that check them.",
            "slots": ["forge_worker", "auditor"]})
        assert outcome["template"]["template_id"] == "template-1"
        assert agent.get_crew_template("template-1").template == "duo"

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_crew_template_book(load_crew_templates())
        assert outcome["count"] == 4
        assert outcome["book"]["template_count"] == 4
        events = _template_events(store, session_id, "crew_template")
        assert [e["template_id"] for e in events] == [
            "tpl-duo", "tpl-full-six",
            "tpl-research-swarm", "tpl-review-panel"]
        rosters = _template_events(
            store, session_id, "crew_formation_roster")
        assert [e["template"] for e in rosters] == [
            "duo", "full_six", "research_swarm", "review_panel"]
        indexes = _template_events(store, session_id, "crew_template_index")
        assert len(indexes) == 1
        assert indexes[0]["total_templates"] == 4
        assert agent.crew_templates().title == (
            "Crew template book at the M-142 slice boundary")
        # The registry holds records, never rosters or
        # indexes: both are derived at call time.
        assert agent.crew_templates().indexes == ()
        assert agent.crew_template_roster("duo").size == 2
        assert agent.crew_template_index().total_slots == 14
        agent.close()

    def test_register_book_twice_refuses(self, agent):
        agent.register_crew_template_book(load_crew_templates())
        with pytest.raises(ValueError):
            agent.register_crew_template_book(load_crew_templates())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_crew_template_book()
        assert outcome["count"] == 4
        assert outcome["book"]["template_count"] == 4
        events = _template_events(store, session_id, "crew_template")
        assert [e["template_id"] for e in events] == [
            "tpl-duo", "tpl-full-six",
            "tpl-research-swarm", "tpl-review-panel"]
        assert len(_template_events(
            store, session_id, "crew_formation_roster")) == 4
        assert len(_template_events(
            store, session_id, "crew_template_index")) == 1
        assert agent.crew_templates().title == (
            "Crew template book at the M-142 slice boundary")
        # The recorded book stands whole: its held
        # index still answers.
        assert agent.crew_templates().indexes[0].index_id == (
            "index-m142-boundary")
        assert agent.crew_template_index().total_templates == 4
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_crew_template_book()
        with pytest.raises(ValueError):
            agent.record_crew_template_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_template_book(tmp_path)
        book = load_crew_templates_file(path)
        outcome = agent.record_crew_template_book(book)
        assert outcome["count"] == 4
        assert agent.crew_templates().title == (
            "Crew template book at the M-142 slice boundary")
        assert agent.get_crew_template("review_panel").size == 2
        assert agent.crew_template_roster("full_six").size == 6

    def test_one_by_one_holdings_stand_under_a_session_book(self, agent):
        agent.register_crew_template(_tpl())
        # Held one by one, the records stand under a
        # session crew template book composed in the
        # agent layer - never under a recorded book
        # title.
        assert agent.crew_templates().title == "Session crew template book"
        agent.register_crew_template(_tpls()[3])
        assert [t.template_id for t in agent.crew_templates().entries] == [
            "tpl-duo", "tpl-review-panel"]
        # A whole book recorded now would re-hold the
        # same template ids: the registry refuses it,
        # as it refuses any duplicate.
        with pytest.raises(ValueError):
            agent.record_crew_template_book()


class TestCrewTemplatesAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_crew_templates()
        assert outcome["book"]["title"] == (
            "Crew template book at the M-142 slice boundary")
        assert outcome["book"]["template_count"] == 4
        assert "tpl-review-panel" in outcome["templates_text"]
        assert "duo - 2 member(s)" in outcome["roster_text"]
        assert "Template index:" in outcome["index_text"]
        assert "Crew templates (M-143)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_crew_template(_tpl())
        outcome = agent.report_crew_templates()
        assert outcome["book"]["template_count"] == 1
        assert "tpl-duo" in outcome["templates_text"]
        assert "tpl-full-six" not in outcome["templates_text"]
        assert "full_six" not in outcome["roster_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_crew_templates()
        registry = agent._crew_templates_registry()
        assert registry.list_templates() == ()
        for kind in ("crew_template", "crew_formation_roster",
                     "crew_template_index"):
            assert _template_events(store, session_id, kind) == []
        agent.close()

    def test_no_live_crew_model_or_persist_road(self, agent):
        # This layer holds the templates as data: it
        # summons no crew, spawns no agent, runs no
        # agent, calls no model, persists nothing - and
        # there is no Part VIII board yet.
        assert not hasattr(agent, "summon_crew_template")
        assert not hasattr(agent, "spawn_crew_template")
        assert not hasattr(agent, "run_crew_template")
        assert not hasattr(agent, "generate_crew_templates")
        assert not hasattr(agent, "persist_crew_templates")
        assert not hasattr(agent, "crew_templates_board")


class TestCrewTemplatesTerminalSurface:
    def test_show_template_member_roster_and_index(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/templates")
        assert "Crew templates (M-143)" in text
        _, _, text = _slash(agent, "/templates template duo")
        assert "tpl-duo: duo" in text
        _, _, text = _slash(agent, "/templates member auditor")
        assert "tpl-duo" in text
        assert "tpl-review-panel" in text
        assert "tpl-research-swarm" not in text
        _, _, text = _slash(agent, "/templates roster full_six")
        assert "full_six - 6 member(s)" in text
        _, _, text = _slash(agent, "/templates index")
        assert "Template index:" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/templates [show|template <template>|member <member-id>|"
                "roster <template>|index]") in text
        _, _, text = _slash(agent, "/templates dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/templates template missing-one")
        assert "no formation answers to the name" in text


@pytest.fixture()
def templates_handler(agent, monkeypatch):
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


def _templates_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCrewTemplatesCommand:
    def test_show_is_default(self, templates_handler, agent):
        templates_handler._handle_templates("")
        assert "Crew templates (M-143)" in _templates_published_text(
            templates_handler)

    def test_template_member_roster_and_index(
            self, templates_handler, agent):
        templates_handler._handle_templates("template tpl-duo")
        assert "forge_worker" in _templates_published_text(templates_handler)
        templates_handler._handle_templates("member scribe")
        assert "tpl-full-six" in _templates_published_text(templates_handler)
        templates_handler._handle_templates("roster duo")
        assert "duo - 2 member(s)" in _templates_published_text(
            templates_handler)
        templates_handler._handle_templates("index")
        assert "Template index:" in _templates_published_text(
            templates_handler)

    def test_bad_grammar_is_published(self, templates_handler, agent):
        templates_handler._handle_templates("dance party")
        assert USAGE in _templates_published_text(templates_handler)


class TestChatScreenRoutingTemplates:
    def test_templates_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/templates template duo", _FakeLog())
        assert calls == [("/templates", "template duo")]
