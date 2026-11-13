"""M-154 Cross-project memory - pure-layer tests.

TIER: integration

The pure layer is the exchange as data: one project's
lessons carried with their provenance whole (the
project learned in, the context learned in, the
evidence stood on), offered to other projects through
explicit offer states - offered, accepted, declined,
withdrawn - never as silent contamination, composed
by import from the shipped project memory map
(M-150) and the shipped session memory (M-153), with
an exchange panel derived from the whole book in
settled order, the shipped example book held in a
data file, and a loader that reads a book from any
file. A lesson stands in a target project only
through an accepted offer, provenance whole. Nothing
here calls a model, writes any project's files or
updates any live memory: holding a lesson or an
offer changes nothing but data.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.project_memory_map import (
    build_entry as build_map_entry,
    load_project_memory_map,
)
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.cross_project_memory import (
    CROSS_PROJECT_RESOURCE,
    CROSS_PROJECT_SCHEMA,
    CROSS_PROJECT_SLICE,
    OFFER_STATES,
    PLAIN_EXPLANATION,
    USAGE,
    CrossProjectBook,
    CrossProjectRegistry,
    ExchangePanel,
    ExchangePanelRow,
    LessonOffer,
    OfferStateCount,
    SharedLesson,
    accepted_lessons,
    book_record,
    build_book,
    build_lesson,
    build_offer,
    build_panel,
    build_row,
    derive_panel,
    format_accepted,
    format_cross_project_screen,
    format_lesson,
    format_lessons,
    format_offers,
    format_panel,
    lesson_from_map_entry,
    lesson_record,
    lessons_from_memory_map,
    lessons_from_session_memory,
    load_cross_project_memory,
    load_cross_project_memory_file,
    normalize_offer_state,
    offer_record,
    panel_plain_words,
    panel_record,
    parse_cross_project_args,
    plain_words,
    validate_book,
    validate_lesson,
    validate_offer,
    validate_panel,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = (
    "Cross-project memory at the M-153 slice boundary")


def _lesson(**overrides):
    fields = {
        "lesson_id": "lesson-test",
        "section": "gotcha",
        "title": "A shared lesson",
        "detail": "The lesson itself, in plain words.",
        "source_project": "project-alpha",
        "context": "Learned while fixing the alpha test suite.",
        "evidence": "The alpha suite's failure log of the day.",
        "source": "test source",
        "ref": "alpha/core/thing.py",
    }
    fields.update(overrides)
    return build_lesson(fields)


def _offer(**overrides):
    fields = {
        "offer_id": "offer-test",
        "lesson_id": "lesson-test",
        "target_project": "project-beta",
        "state": "offered",
        "note": "Standing until the target's word.",
    }
    fields.update(overrides)
    return build_offer(fields)


def _stored_lesson(lesson):
    record = lesson.to_record()
    record.pop("type")
    record.pop("slice")
    return record


def _stored_offer(offer):
    record = offer.to_record()
    record.pop("type")
    record.pop("slice")
    return record


def _stored_panel(panel):
    record = panel.to_record()
    record.pop("type")
    record.pop("slice")
    for row in record["rows"]:
        row.pop("type")
        row.pop("slice")
    return record


def _book(lessons=None, offers=None, **overrides):
    fields = {
        "title": "A test cross-project book",
        "lessons": [_stored_lesson(item) for item in (
            lessons if lessons is not None else [_lesson()])],
        "offers": [_stored_offer(item) for item in (
            offers if offers is not None else [_offer()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "cross_project_memory.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert CROSS_PROJECT_SLICE == "M-154"
    assert CROSS_PROJECT_SCHEMA == "mythic.cross_project_memory/1"
    assert CROSS_PROJECT_RESOURCE == "cross_project_memory.yaml"
    assert OFFER_STATES == (
        "offered", "accepted", "declined", "withdrawn")
    assert "provenance" in PLAIN_EXPLANATION
    assert "never as silent contamination" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /crossmemory")
    assert "accepted <project>" in USAGE


def test_shipped_example_shape():
    book = load_cross_project_memory()
    assert isinstance(book, CrossProjectBook)
    assert book.title == EXAMPLE_TITLE
    assert book.lesson_ids() == (
        "lesson-commit-before-answer", "lesson-reap-at-bank",
        "lesson-bank-incrementally")
    assert book.offer_ids() == (
        "offer-reap-to-samverk", "offer-commit-to-mythic",
        "offer-bank-to-samtal")
    assert book.total_lessons == 3
    assert book.total_offers == 3
    first = book.lessons[0]
    # The first lesson stands with its provenance whole:
    # learned in Samtal, in a named context, on evidence.
    assert first.source_project == "samtal"
    assert first.section == "gotcha"
    assert "Gatekeeper" in first.context
    assert first.evidence
    assert first.ref == "samtal-mvp/server.py"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_cross_project_memory()
    panel = book.panel_for("panel-m153-boundary")
    derived = derive_panel(book)
    assert validate_panel(panel, book) == panel
    assert panel.rows == derived.rows
    assert [row.lesson_id for row in panel.rows] == [
        "lesson-reap-at-bank", "lesson-commit-before-answer",
        "lesson-bank-incrementally"]
    assert [row.state for row in panel.rows] == [
        "accepted", "offered", "declined"]
    assert panel.total_items == 3
    assert panel.total_accepted == 1
    assert panel.total_offered == 1
    assert panel.total_declined == 1
    assert panel.total_withdrawn == 0
    assert panel.account[0] == (
        "The exchange panel holds 3 offers: accepted 1, "
        "offered 1, declined 1, withdrawn 0.")


def test_lesson_validation_and_aliases():
    lesson = build_lesson({
        "id": "lesson-alias", "kind": "gotchas",
        "name": "An aliased lesson", "body": "The body stands.",
        "from_project": "project-alpha",
        "learned_in": "A context.", "proof": "Some evidence.",
        "source": "a source", "path": "alpha/x.py"})
    assert lesson.lesson_id == "lesson-alias"
    assert lesson.section == "gotcha"
    assert lesson.title == "An aliased lesson"
    assert lesson.detail == "The body stands."
    assert lesson.source_project == "project-alpha"
    assert lesson.context == "A context."
    assert lesson.evidence == "Some evidence."
    assert lesson.ref == "alpha/x.py"
    with pytest.raises(ValueError):
        build_lesson({
            "section": "gotcha", "title": "Two titles",
            "name": "A different title", "detail": "D.",
            "source_project": "project-alpha", "context": "C.",
            "evidence": "E.", "source": "S", "ref": "a/b.py"})


def test_lesson_composes_the_shipped_map_entry():
    entry = build_map_entry({
        "entry_id": "map-test-trap", "section": "gotcha",
        "title": "A library trap",
        "detail": "The trap itself, in plain words.",
        "source": "the map", "ref": "alpha/lib.py"})
    lesson = lesson_from_map_entry(
        entry, source_project="project-alpha",
        context="Learned the day the trap fired.",
        evidence="The trap's own traceback.")
    assert isinstance(lesson, SharedLesson)
    assert lesson.lesson_id == "map-test-trap"
    assert lesson.section == "gotcha"
    assert lesson.title == "A library trap"
    assert lesson.detail == entry.detail
    assert lesson.source == entry.source
    assert lesson.ref == entry.ref
    assert lesson.source_project == "project-alpha"


def test_lesson_without_provenance_refuses():
    entry = build_map_entry({
        "entry_id": "map-lonely", "section": "gotcha",
        "title": "A fact at home", "detail": "It stays home.",
        "source": "the map", "ref": "alpha/lib.py"})
    # A bare entry names no provenance: it does not travel.
    with pytest.raises(TypeError):
        lesson_from_map_entry(entry)
    with pytest.raises(ValueError):
        validate_lesson(entry, source_project="project-alpha")
    record = _stored_lesson(_lesson())
    record.pop("evidence")
    with pytest.raises(ValueError):
        build_lesson(record)
    record = _stored_lesson(_lesson())
    record.pop("context")
    with pytest.raises(ValueError):
        build_lesson(record)
    record = _stored_lesson(_lesson())
    record.pop("source_project")
    with pytest.raises(ValueError):
        build_lesson(record)


def test_lesson_refusals():
    with pytest.raises(ValueError):
        build_lesson(_stored_lesson(_lesson()), bogus="x")
    with pytest.raises(ValueError):
        _lesson(section="nonsense")
    with pytest.raises(ValueError):
        _lesson(source_project="two words")
    with pytest.raises(ValueError):
        _lesson(detail="")
    with pytest.raises(ValueError):
        _lesson(ref="has a space.py")


def test_offer_states_and_aliases():
    assert normalize_offer_state("offered") == "offered"
    assert normalize_offer_state("Pending") == "offered"
    assert normalize_offer_state("taken") == "accepted"
    assert normalize_offer_state("REJECTED") == "declined"
    assert normalize_offer_state("retracted") == "withdrawn"
    with pytest.raises(ValueError):
        normalize_offer_state("smuggled")
    offer = build_offer(_lesson(), target_project="project-beta",
                        state="pending", note="A standing offer.")
    assert offer.lesson_id == "lesson-test"
    assert offer.state == "offered"
    aliased = build_offer({
        "id": "offer-alias", "lesson": "lesson-test",
        "to_project": "project-beta", "status": "taken",
        "detail": "The target took it."})
    assert aliased.state == "accepted"
    assert aliased.note == "The target took it."


def test_offer_refusals():
    with pytest.raises(ValueError):
        build_offer(_stored_offer(_offer()), bogus="x")
    with pytest.raises(ValueError):
        _offer(state="smuggled")
    record = _stored_offer(_offer())
    record.pop("note")
    with pytest.raises(ValueError):
        build_offer(record)
    with pytest.raises(ValueError):
        build_offer(_lesson(lesson_id=None),
                    target_project="project-beta",
                    state="offered", note="No id to name.")


def test_book_judges_offers_against_lessons():
    # An offer to the lesson's own project is no
    # cross-project offer at all.
    with pytest.raises(ValueError):
        _book(offers=[_offer(target_project="project-alpha")])
    # An offer naming a lesson the book does not hold.
    with pytest.raises(ValueError):
        _book(offers=[_offer(lesson_id="lesson-missing")])
    # The same lesson offered twice to one target.
    with pytest.raises(ValueError):
        _book(offers=[_offer(), _offer(offer_id="offer-two")])
    # A duplicated lesson id, and one fact named twice
    # by one project, both refuse.
    with pytest.raises(ValueError):
        _book(lessons=[_lesson(), _lesson(
            title="Another title", ref="alpha/other.py")],
            offers=[])
    with pytest.raises(ValueError):
        _book(lessons=[_lesson(), _lesson(
            lesson_id="lesson-two", ref="alpha/other.py")],
            offers=[])
    # Totals that are not the records' own counts refuse.
    with pytest.raises(ValueError):
        _book(total_lessons=7)


def test_book_lookups():
    book = _book()
    assert book.lesson_for("lesson-test").title == "A shared lesson"
    assert book.offer_for("offer-test").state == "offered"
    with pytest.raises(KeyError):
        book.lesson_for("lesson-nope")
    with pytest.raises(KeyError):
        book.offer_for("offer-nope")
    with pytest.raises(KeyError):
        book.panel_for("panel-nope")


def test_panel_is_derived_in_settled_order():
    lessons = [
        _lesson(lesson_id="lesson-zed", title="Zed's lesson",
                source_project="project-zed"),
        _lesson(lesson_id="lesson-alpha", title="Alpha's lesson",
                source_project="project-alpha"),
        _lesson(lesson_id="lesson-mid", title="Mid's lesson",
                source_project="project-mid"),
        _lesson(lesson_id="lesson-gone", title="Gone's lesson",
                source_project="project-gone"),
    ]
    offers = [
        _offer(offer_id="offer-w", lesson_id="lesson-gone",
               target_project="project-beta", state="withdrawn"),
        _offer(offer_id="offer-d", lesson_id="lesson-mid",
               target_project="project-beta", state="declined"),
        _offer(offer_id="offer-o", lesson_id="lesson-zed",
               target_project="project-beta", state="offered"),
        _offer(offer_id="offer-a", lesson_id="lesson-alpha",
               target_project="project-beta", state="accepted"),
    ]
    book = _book(lessons=lessons, offers=offers)
    panel = derive_panel(book)
    assert [row.state for row in panel.rows] == [
        "accepted", "offered", "declined", "withdrawn"]
    assert [row.lesson_id for row in panel.rows] == [
        "lesson-alpha", "lesson-zed", "lesson-mid", "lesson-gone"]
    assert panel.total_items == 4
    assert panel.state_counts == tuple(
        OfferStateCount(state=state, items=1)
        for state in ("accepted", "offered", "declined", "withdrawn"))
    row = panel.row_for("lesson-alpha", "project-beta")
    assert row.source_project == "project-alpha"
    assert row.title == "Alpha's lesson"
    with pytest.raises(KeyError):
        panel.row_for("lesson-alpha", "project-zed")


def test_panel_judgement_against_its_book():
    book = _book()
    panel = derive_panel(book)
    assert validate_panel(_stored_panel(panel), book) == panel
    tampered = _stored_panel(panel)
    tampered["rows"][0]["title"] = "A softened title"
    with pytest.raises(ValueError):
        validate_panel(tampered, book)
    tampered = _stored_panel(panel)
    tampered["rows"][0]["source_project"] = "project-zed"
    with pytest.raises(ValueError):
        validate_panel(tampered, book)


def test_panel_construction_refusals():
    book = _book(offers=[
        _offer(),
        _offer(offer_id="offer-two", lesson_id="lesson-test",
               target_project="project-gamma", state="accepted")])
    panel = derive_panel(book)
    rows = list(panel.rows)
    with pytest.raises(ValueError):
        ExchangePanel(
            rows=list(reversed(rows)), total_items=2,
            total_accepted=1, total_offered=1, total_declined=0,
            total_withdrawn=0, state_counts=panel.state_counts,
            account=panel.account)
    with pytest.raises(ValueError):
        ExchangePanel(
            rows=rows, total_items=3,
            total_accepted=1, total_offered=1, total_declined=0,
            total_withdrawn=0, state_counts=panel.state_counts,
            account=panel.account)
    with pytest.raises(ValueError):
        build_panel({
            "rows": [_stored_panel(panel)["rows"][0]],
            "total_items": 1, "total_accepted": 0,
            "total_offered": 1, "total_declined": 0,
            "total_withdrawn": 0,
            "state_counts": [{"state": "offered", "items": 1}]})


def test_panel_row_judged_against_its_offer_and_lesson():
    lesson = _lesson()
    offer = _offer()
    row = build_row({
        "state": "offered", "lesson_id": "lesson-test",
        "title": lesson.title, "detail": lesson.detail,
        "source_project": "project-alpha",
        "target_project": "project-beta"}, offer, lesson)
    assert isinstance(row, ExchangePanelRow)
    with pytest.raises(ValueError):
        validate_row({
            "state": "accepted", "lesson_id": "lesson-test",
            "title": lesson.title, "detail": lesson.detail,
            "source_project": "project-alpha",
            "target_project": "project-beta"}, offer, lesson)


def test_lessons_from_the_shipped_map():
    map_book = load_project_memory_map()
    lessons = lessons_from_memory_map(
        map_book, source_project="mythic-coder",
        context="The campaign's own memory map, read whole.",
        evidence="The shipped map book itself.")
    assert len(lessons) == len(map_book.entries)
    assert [item.lesson_id for item in lessons] == [
        entry.entry_id for entry in map_book.entries]
    assert all(
        item.source_project == "mythic-coder" for item in lessons)
    assert {item.section for item in lessons} == {
        entry.section for entry in map_book.entries}


def test_lessons_from_session_memory():
    memory_book = load_session_memory()
    lessons = lessons_from_session_memory(
        memory_book, source_project="mythic-coder",
        context="Facts a session carried across its days.",
        evidence="The shipped session-memory book itself.")
    assert [item.lesson_id for item in lessons] == [
        "note-connected-code", "note-reap-at-bank",
        "note-campaign-home"]
    assert all(
        item.context == "Facts a session carried across its days."
        for item in lessons)


def test_accepted_lessons_stand_only_through_acceptance():
    book = load_cross_project_memory()
    # The accepted offer stands in Samverk, provenance whole.
    standing = accepted_lessons(book, "samverk")
    assert [item.lesson_id for item in standing] == [
        "lesson-reap-at-bank"]
    assert standing[0].source_project == "mythic-coder"
    assert standing[0].evidence
    # The declined lesson stands nowhere in Samtal, and
    # the merely-offered lesson stands nowhere yet in
    # the coder: no silent contamination either way.
    assert accepted_lessons(book, "samtal") == ()
    assert accepted_lessons(book, "mythic-coder") == ()
    assert accepted_lessons(book, "project-nowhere") == ()


def test_book_validation_refusals():
    raw = _shipped_raw()
    with pytest.raises(ValidationError):
        validate_book({**raw, "schema": "mythic.other/9"})
    with pytest.raises(ValidationError):
        validate_book({**raw, "bogus": 1})
    broken = {**raw, "lessons": []}
    with pytest.raises(ValidationError):
        validate_book(broken)
    broken = {**raw, "guide": {"title": "T", "bogus": 1}}
    with pytest.raises(ValidationError):
        validate_book(broken)
    # A stored panel that disagrees with its book refuses.
    import copy
    broken = copy.deepcopy(raw)
    broken["panels"][0]["rows"][0]["title"] = "A rewritten lesson"
    with pytest.raises(ValidationError):
        validate_book(broken)
    # The example check holds the shipped file to its pins.
    with pytest.raises(ValidationError):
        validate_book(raw, require_example=False) \
            if False else validate_book(
                {**raw, "guide": {"title": "Another title"}},
                require_example=True)


def test_load_cross_project_memory_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "cross_project_memory.yaml").read_text(encoding="utf-8")
    path = tmp_path / "cross_project_memory.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_cross_project_memory_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.lesson_ids()[0] == "lesson-commit-before-answer"
    with pytest.raises(FileNotFoundError):
        load_cross_project_memory_file(tmp_path / "missing.yaml")


def test_registry_holds_lessons_and_offers_one_by_one():
    registry = CrossProjectRegistry()
    lesson = registry.register_lesson({
        "section": "gotcha", "title": "Held lesson",
        "detail": "Held one by one.",
        "source_project": "project-alpha",
        "context": "A registry test.", "evidence": "This test.",
        "source": "test", "ref": "alpha/x.py"})
    assert lesson.lesson_id == "lesson-1"
    with pytest.raises(ValueError):
        registry.register_offer({
            "lesson_id": "lesson-missing",
            "target_project": "project-beta", "state": "offered",
            "note": "No lesson stands there."})
    with pytest.raises(ValueError):
        registry.register_offer({
            "lesson_id": "lesson-1",
            "target_project": "project-alpha", "state": "offered",
            "note": "It never left home."})
    offer = registry.register_offer({
        "lesson_id": "lesson-1",
        "target_project": "project-beta", "state": "accepted",
        "note": "The target took it."})
    assert offer.offer_id == "offer-1"
    with pytest.raises(ValueError):
        registry.register_offer({
            "lesson_id": "lesson-1",
            "target_project": "project-beta", "state": "offered",
            "note": "Twice to one target."})
    assert [item.lesson_id for item in registry.list_lessons()] == [
        "lesson-1"]
    panel = registry.panel()
    assert panel.total_items == 1
    assert panel.total_accepted == 1
    assert [item.lesson_id for item in
            registry.accepted_lessons("project-beta")] == ["lesson-1"]
    assert registry.accepted_lessons("project-gamma") == ()
    with pytest.raises(KeyError):
        registry.get_lesson("lesson-nope")


def test_registry_register_book_titles():
    registry = CrossProjectRegistry()
    registry.register_book(load_cross_project_memory())
    assert registry.book().title == EXAMPLE_TITLE
    with pytest.raises(ValueError):
        registry.register_book(load_cross_project_memory())
    other = CrossProjectRegistry()
    other.register_lesson(_lesson())
    with pytest.raises(ValueError):
        other.register_book(_book(title="Another title"))


def test_records_and_plain_words():
    lesson = _lesson()
    lesson_news = lesson_record(lesson)
    assert lesson_news["type"] == "cross_project_lesson"
    assert lesson_news["news"] is True
    assert "project-alpha" in lesson_news["headline"]
    offer_news = offer_record(_offer())
    assert offer_news["type"] == "cross_project_offer"
    assert "project-beta" in offer_news["headline"]
    book = _book()
    panel_news = panel_record(derive_panel(book), book)
    assert panel_news["type"] == "cross_project_panel"
    book_news = book_record(book)
    assert book_news["type"] == "cross_project_book"
    assert book_news["lesson_count"] == 1
    assert book_news["offer_count"] == 1
    words = plain_words(lesson)
    assert "learned in project-alpha" in words
    assert "The alpha suite's failure log" in words
    told = panel_plain_words(book)
    assert "A test cross-project book" in told
    assert "lesson-test: offered" in told


def test_formatters_and_screen():
    book = load_cross_project_memory()
    assert "lesson-reap-at-bank" in format_lesson(
        book.lesson_for("lesson-reap-at-bank"))
    assert "learned in samtal" in format_lesson(
        book.lesson_for("lesson-commit-before-answer"))
    assert "lesson-bank-incrementally" in format_lessons(book)
    offers_text = format_offers(book)
    assert "offer-reap-to-samverk" in offers_text
    assert "accepted" in offers_text
    accepted_text = format_accepted(book, "samverk")
    assert "lesson-reap-at-bank" in accepted_text
    assert "mythic-coder" in accepted_text
    assert format_accepted(book, "samtal") == (
        "No lessons stand accepted into samtal.")
    panel_text = format_panel(book)
    assert "Exchange panel in Cross-project memory" in panel_text
    screen = format_cross_project_screen()
    assert "Cross-Project Memory (M-154)" in screen
    assert "lesson-commit-before-answer" in screen
    assert USAGE in screen


def test_parse_cross_project_args_grammar():
    assert parse_cross_project_args("") == ("show", None)
    assert parse_cross_project_args("show") == ("show", None)
    assert parse_cross_project_args("list") == ("show", None)
    assert parse_cross_project_args(
        "lesson lesson-test") == ("lesson", "lesson-test")
    assert parse_cross_project_args("offers") == ("offers", None)
    assert parse_cross_project_args(
        "accepted samverk") == ("accepted", "samverk")
    assert parse_cross_project_args("panel") == ("panel", None)
    for bad in ("dance", "lesson", "accepted",
                "lesson two words", "offers now"):
        with pytest.raises(ValueError):
            parse_cross_project_args(bad)


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "cross_project_memory.py").read_text(encoding="utf-8")
    # The pure layer composes the shipped project
    # memory map and session memory by import, and
    # imports no agent, ui or terminal code: holding
    # a lesson or an offer can call no model, write
    # no project's files and contaminate nothing.
    assert "from .project_memory_map import" in source
    assert "from .session_memory import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


# -- agent layer -----------------------------------------------------------
#
# M-154 agent layer: the agent holds a
# CrossProjectRegistry for the session (session state
# only, no new setting), lessons and offers are held
# by being registered - published as their
# lesson_record / offer_record session news with the
# derived panel_record, through the checkpoint road,
# deduped per shape - the report road renders the held
# book (or the shipped example when unheld) through
# the pure formatters, an offer road reads the
# session's project memory map book onto lessons and
# offers them onward to a named target, and the
# /crossmemory surface rides both roads on the pure
# parser + formatters. Status, get, panel and accepted
# reads register and publish nothing, answer from the
# held registry first and from the shipped example
# only while nothing is held - a held session never
# falls back to the example. The panel derives at call
# time from the whole book, never held. This layer
# calls no model, writes no project's files and enters
# nothing into any project's memory, and there is no
# Part VIII board yet, so the screen is where the
# exchange is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _cross_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_cross_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "cross_project_memory.yaml").read_text(encoding="utf-8")
    path = tmp_path / "cross_project_memory.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCrossProjectAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.cross_project_status()
        assert status["lessons"] == []
        assert status["offers"] == []
        assert status["book"] is None
        assert status["cross_project"]["title"] == EXAMPLE_TITLE
        assert len(status["cross_project"]["lessons"]) == 3
        assert status["panel"]["total_items"] == 3
        assert status["panel"]["total_accepted"] == 1
        assert status["panels"][0]["panel_id"] == (
            "panel-m153-boundary")
        assert status["book_record"]["lesson_count"] == 3
        assert "Cross-Project Memory (M-154)" in (
            status["screen"])
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._cross_project_registry()
        assert agent._cross_project_registry() is first
        assert agent._cross_project_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.cross_project_status()
        agent.get_cross_project_lesson("lesson-reap-at-bank")
        agent.get_cross_project_offer("offer-reap-to-samverk")
        agent.cross_project_panel()
        agent.accepted_cross_project_lessons("samverk")
        agent.report_cross_project_memory()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("cross_project")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_cross_project_lesson("lesson-nope")
        with pytest.raises(KeyError):
            agent.get_cross_project_offer("offer-nope")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_cross_project_lesson(_lesson())
        status = agent.cross_project_status()
        assert [item["lesson_id"] for item in status["lessons"]] == [
            "lesson-test"]
        assert status["book"]["title"] == (
            "Cross-project memory")

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_cross_project_lesson(_lesson())
        with pytest.raises(KeyError):
            agent.get_cross_project_lesson("lesson-reap-at-bank")
        lesson = agent.get_cross_project_lesson("lesson-test")
        assert lesson.title == "A shared lesson"
        assert agent.cross_project_book().title == (
            "Cross-project memory")


class TestCrossProjectAgentHolding:
    def test_register_lesson_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_cross_project_lesson(_lesson())
        assert outcome["lesson"]["lesson_id"] == "lesson-test"
        assert outcome["lesson_news"]["type"] == (
            "cross_project_lesson")
        events = _cross_events(
            store, session_id, "cross_project_lesson")
        assert len(events) == 1
        assert events[0]["lesson_id"] == "lesson-test"
        agent._publish_cross_project_record(
            outcome["lesson_news"])
        assert len(_cross_events(
            store, session_id, "cross_project_lesson")) == 1
        agent._publish_cross_project_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_cross_project_record(
            book_record(load_cross_project_memory()))
        for kind in ("mentions_mention", "cross_project_book"):
            assert _cross_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_lesson_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_cross_project_lesson(_lesson())
        with pytest.raises(ValueError):
            agent.register_cross_project_lesson(_lesson())
        assert len(_cross_events(
            store, session_id, "cross_project_lesson")) == 1
        agent.close()

    def test_register_offer_holds_and_publishes_offer_and_panel(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_cross_project_lesson(_lesson())
        outcome = agent.register_cross_project_offer(_offer(
            offer_id=None, state="accepted"))
        assert outcome["offer"]["state"] == "accepted"
        assert outcome["panel_record"]["type"] == (
            "cross_project_panel")
        offers = _cross_events(
            store, session_id, "cross_project_offer")
        assert len(offers) == 1
        panels = _cross_events(
            store, session_id, "cross_project_panel")
        assert len(panels) == 1
        assert panels[0]["total_items"] == 1
        standing = agent.accepted_cross_project_lessons(
            "project-beta")
        assert [item.lesson_id for item in standing] == [
            "lesson-test"]
        assert standing[0].source_project == "project-alpha"
        agent.close()

    def test_offer_refusals_hold_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValueError):
            agent.register_cross_project_offer(_offer())
        agent.register_cross_project_lesson(_lesson())
        with pytest.raises(ValueError):
            agent.register_cross_project_offer(_offer(
                target_project="project-alpha"))
        assert _cross_events(
            store, session_id, "cross_project_offer") == []
        agent.close()

    def test_offer_memory_map_lessons_composes_the_map(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        map_book = load_project_memory_map()
        outcome = agent.offer_memory_map_lessons(
            "samverk", source_project="mythic-coder",
            context="The coder campaign's own map, read whole.",
            evidence="The shipped project memory map book.")
        assert outcome["count"] == len(map_book.entries)
        assert len(_cross_events(
            store, session_id, "cross_project_lesson")) == len(
                map_book.entries)
        assert len(_cross_events(
            store, session_id, "cross_project_offer")) == len(
                map_book.entries)
        # Every offer stands in the offered state: nothing
        # has entered Samverk, and nothing can until an
        # acceptance is recorded - no silent contamination.
        book = agent.cross_project_book()
        assert {offer.state for offer in book.offers} == {"offered"}
        assert agent.accepted_cross_project_lessons(
            "samverk") == ()
        assert {lesson.source_project for lesson in book.lessons} == {
            "mythic-coder"}
        with pytest.raises(ValueError):
            agent.offer_memory_map_lessons(
                "samtal", source_project="mythic-coder",
                context="Again.", evidence="Again.")
        agent.close()

    def test_offer_memory_map_lessons_refuses_its_own_project(
            self, agent):
        with pytest.raises(ValueError):
            agent.offer_memory_map_lessons(
                "mythic-coder", source_project="mythic-coder",
                context="A context.", evidence="Some evidence.")
        assert agent._cross_project_registry().list_lessons() == ()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_cross_project_book(book)
        assert outcome["count"] == 1
        assert outcome["offer_count"] == 1
        assert [item["type"] for item in outcome["lessons_news"]] == [
            "cross_project_lesson"]
        assert [item["type"] for item in outcome["offers_news"]] == [
            "cross_project_offer"]
        assert agent.cross_project_book().title == (
            "A test cross-project book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_cross_project_book(
            load_cross_project_memory())
        with pytest.raises(ValueError):
            agent.register_cross_project_book(
                load_cross_project_memory())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_cross_project_book()
        assert outcome["count"] == 3
        assert outcome["offer_count"] == 3
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_cross_events(
            store, session_id, "cross_project_lesson")) == 3
        assert len(_cross_events(
            store, session_id, "cross_project_offer")) == 3
        assert agent.cross_project_book().panels[0].panel_id == (
            "panel-m153-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_cross_project_book()
        with pytest.raises(ValueError):
            agent.record_cross_project_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_cross_book(tmp_path)
        book = load_cross_project_memory_file(path)
        outcome = agent.record_cross_project_book(book)
        assert outcome["count"] == 3
        assert agent.get_cross_project_lesson(
            "lesson-reap-at-bank").title == (
                "Verify copies are reaped at bank")

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_cross_project_memory()
        assert report["book"]["lesson_count"] == 3
        assert "lesson-reap-at-bank" in report["lessons_text"]
        assert "Exchange panel in Cross-project" in (
            report["panel_text"])

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_cross_project_lesson(_lesson())
        report = agent.report_cross_project_memory()
        assert report["book"]["title"] == (
            "Cross-project memory")
        assert "lesson-reap-at-bank" not in report["lessons_text"]
        assert "lesson-test" in report["lessons_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_cross_project_memory()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("cross_project")] == []
        agent.close()

    def test_no_live_write_or_persist_road(
            self, agent, tmp_path):
        # This layer holds lessons and offers as data: it
        # calls no model, writes no project's files,
        # enters nothing into any project's own memory
        # and persists nothing - and there is no Part
        # VIII board yet. Holding, recording or offering
        # changes no workspace file and no live context.
        assert not hasattr(agent, "apply_cross_project_memory")
        assert not hasattr(agent, "edit_cross_project_memory")
        assert not hasattr(agent, "persist_cross_project_memory")
        assert not hasattr(agent, "import_cross_project_lesson")
        assert not hasattr(agent, "cross_project_board")
        (tmp_path / "alpha.py").write_text(
            "def greet(name):\n    return name\n", encoding="utf-8")
        before = {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")}
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        built_before = builder.build()
        agent.register_cross_project_lesson(_lesson())
        agent.record_cross_project_book()
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestCrossProjectTerminalSurface:
    def test_show_lesson_offers_accepted_panel(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/crossmemory")
        assert "Cross-Project Memory (M-154)" in text
        _, _, text = _slash(
            agent, "/crossmemory lesson lesson-reap-at-bank")
        assert "Verify copies are reaped at bank" in text
        _, _, text = _slash(agent, "/crossmemory offers")
        assert "offer-reap-to-samverk" in text
        _, _, text = _slash(agent, "/crossmemory accepted samverk")
        assert "lesson-reap-at-bank" in text
        _, _, text = _slash(agent, "/crossmemory accepted samtal")
        assert "No lessons stand accepted into samtal." in text
        _, _, text = _slash(agent, "/crossmemory panel")
        assert "Exchange panel in Cross-project" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/crossmemory [show|lesson <lesson-id>"
                "|offers|accepted <project>|panel]") in text
        _, _, text = _slash(agent, "/crossmemory dance party")
        assert text == USAGE
        _, _, text = _slash(
            agent, "/crossmemory lesson lesson-nope")
        assert "no lesson in the book" in text


@pytest.fixture()
def crossmemory_handler(agent, monkeypatch):
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


def _crossmemory_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCrossProjectCommand:
    def test_show_is_default(self, crossmemory_handler, agent):
        crossmemory_handler._handle_crossmemory("")
        assert "Cross-Project Memory (M-154)" in (
            _crossmemory_published_text(crossmemory_handler))

    def test_lesson_offers_accepted_panel(
            self, crossmemory_handler, agent):
        crossmemory_handler._handle_crossmemory(
            "lesson lesson-reap-at-bank")
        assert "Verify copies are reaped at bank" in (
            _crossmemory_published_text(crossmemory_handler))
        crossmemory_handler._handle_crossmemory("offers")
        assert "offer-reap-to-samverk" in (
            _crossmemory_published_text(crossmemory_handler))
        crossmemory_handler._handle_crossmemory("accepted samverk")
        assert "lesson-reap-at-bank" in (
            _crossmemory_published_text(crossmemory_handler))
        crossmemory_handler._handle_crossmemory("panel")
        assert "Exchange panel in Cross-project" in (
            _crossmemory_published_text(crossmemory_handler))

    def test_bad_grammar_is_published(self, crossmemory_handler, agent):
        crossmemory_handler._handle_crossmemory("dance party")
        assert USAGE in _crossmemory_published_text(crossmemory_handler)


class TestChatScreenRoutingCrossProject:
    def test_crossmemory_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command(
            "/crossmemory lesson lesson-reap-at-bank",
            _FakeLog())
        assert calls == [(
            "/crossmemory", "lesson lesson-reap-at-bank")]
