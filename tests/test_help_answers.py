"""M-186 Help That Answers - pure-layer tests.

TIER: integration

The pure layer is help that answers, held as
data: one help entry per screen, held whole -
under the screen it stands for in the closed
vocabulary, its title and its detail - and the
local docs the question box answers from, held
whole under their titles, topics and standings,
current or stale. Answers are derived at call
time from the held docs alone: a question
matching a current doc is answered from that
doc's own words, a question matching only a stale
doc stands unanswered and named stale in its
gaps, and a question matching no held doc stands
honestly unanswered. A record claiming a live
search, a network lookup or a model answer
refuses by name, and a stored answer or verdict
refuses by name. The panel is derived for one
held view and the verdict is derived for the
whole book under one view. The shipped example
book is held in a data file, and a loader reads
a book from any file. This layer searches
nothing live, calls no model, opens no network
and writes nothing: it holds help as data and
tells it.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.help_answers import (
    ASK_ACTION,
    EXAMPLE_QUESTION,
    HELP_ANSWERS_RESOURCE,
    HELP_ANSWERS_SCHEMA,
    HELP_ANSWERS_SLICE,
    LOCAL_DOCS_RULE,
    PLAIN_EXPLANATION,
    SCREENS,
    STANDING_WORDS,
    TOPICS,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    DocRecord,
    HelpBook,
    HelpPanel,
    HelpRegistry,
    HelpVerdict,
    HelpView,
    ScreenHelp,
    answer_plain_words,
    answer_record,
    book_record,
    build_book,
    build_doc,
    build_panel,
    build_row,
    build_screen_help,
    build_verdict,
    build_view,
    coverage_plain_words,
    coverage_record,
    covered_screens,
    derive_answer,
    derive_coverage,
    derive_panel,
    derive_verdict,
    doc_gaps,
    doc_passes,
    doc_plain_words,
    doc_record,
    docs_for_standing,
    format_answer,
    format_book,
    format_coverage,
    format_doc,
    format_help_answers_screen,
    format_panel,
    format_screen,
    format_screen_help,
    format_verdict,
    format_view,
    help_for_screen,
    inspect_help_source,
    load_help_answers,
    load_help_answers_file,
    normalize_screen,
    normalize_standing,
    normalize_topic,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_help_args,
    passing_docs,
    plain_lines,
    plain_words,
    screen_record,
    segment_of,
    shown_docs,
    total_docs,
    uncovered_screens,
    validate_book,
    validate_doc,
    validate_panel,
    validate_row,
    validate_screen_help,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "Help that answers at the M-185 slice boundary"


def _doc(**overrides):
    fields = {
        "doc_id": "doc-test",
        "seq": 1,
        "title": "A test doc",
        "topic": "providers and keys",
        "standing": "current",
        "detail": "A test doc held as data, for the tests.",
        "keywords": ["provider", "key"],
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_doc(fields)


def _stored_doc(doc):
    return doc.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _help(**overrides):
    fields = {
        "help_id": "help-test",
        "seq": 1,
        "screen": "chat",
        "title": "A test screen help",
        "detail": "A test screen help held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_screen_help(fields)


def _book(docs=None, views=None, helps=None, **overrides):
    fields = {
        "schema": HELP_ANSWERS_SCHEMA,
        "slice": "M-186",
        "guide": {"title": "A test help book"},
        "docs": [_stored_doc(item) for item in (
            docs if docs is not None else [_doc()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "helps": [item.to_record() for item in (helps or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(docs=[
        _doc(),
        _doc(doc_id="doc-stale", seq=2, title="Commands the sandbox allows",
             topic="sandbox and safety", standing="stale",
             keywords=["sandbox", "command"]),
    ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_help_answers()
    assert book.title == EXAMPLE_TITLE
    assert book.doc_ids() == (
        "doc-undo-commit", "doc-first-task", "doc-provider-keys",
        "doc-crew-dealing", "doc-sandbox-commands", "doc-plain-words")
    assert [v.view_id for v in book.views] == ["view-all", "view-current"]
    assert [h.screen for h in book.helps] == [
        "chat", "terminal", "editor", "lessons"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m185-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == list(book.doc_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.standing_counts} == {
        "current": 5, "stale": 1}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 5
    assert derive_verdict(book, "view-current").verdict == "open"
    assert derive_verdict(book, "view-current").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / HELP_ANSWERS_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == HELP_ANSWERS_SCHEMA
    assert raw["slice"] == "M-186"
    assert "verdict" not in raw
    assert "answer" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-186")]
    assert slice_.title == "Help that answers"
    assert slice_.part == 8
    assert "gives help" in slice_.summary
    assert "for that screen" in slice_.summary
    assert "how do I undo a commit?" in slice_.summary
    assert "local docs" in slice_.summary
    assert HELP_ANSWERS_SLICE == "M-186"


def test_charter_names_no_row_for_m186():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-186") == 0


def test_closed_vocabularies():
    assert STANDING_WORDS == ("current", "stale")
    assert SCREENS == (
        "chat", "terminal", "editor", "review", "settings",
        "onboarding", "lessons", "command palace")
    assert TOPICS == (
        "getting started", "editing and undo", "providers and keys",
        "files and workspace", "crews and parallel work",
        "memory and context", "sandbox and safety", "plain language")
    assert VIEW_FILTERS == ("all", "current", "stale")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert ASK_ACTION == "ask"
    assert EXAMPLE_QUESTION == "how do I undo a commit?"
    assert normalize_standing("CURRENT") == "current"
    assert normalize_topic("Editing and Undo") == "editing and undo"
    assert normalize_screen("Command Palace") == "command palace"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_standing("maybe")
    with pytest.raises(ValueError):
        normalize_topic("a guess")
    with pytest.raises(ValueError):
        normalize_screen("the void")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "local docs held on this machine alone" in LOCAL_DOCS_RULE
    assert "M-186" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /helpask")


def test_shipped_book_judged_honestly_as_data():
    book = load_help_answers()
    undo = book.doc_for("doc-undo-commit")
    assert doc_passes(undo) is True
    assert doc_gaps(undo) == ()
    assert plain_lines(undo) == (
        "Doc: Undo a commit",
        "Topic: editing and undo",
        "Standing: current")
    sandbox = book.doc_for("doc-sandbox-commands")
    assert doc_gaps(sandbox) == ("stale",)
    assert doc_passes(sandbox) is False
    assert [d.doc_id for d in passing_docs(book)] == [
        "doc-undo-commit", "doc-first-task", "doc-provider-keys",
        "doc-crew-dealing", "doc-plain-words"]
    assert total_docs(book) == 6
    assert covered_screens(book) == (
        "chat", "terminal", "editor", "lessons")
    assert uncovered_screens(book) == (
        "review", "settings", "onboarding", "command palace")
    assert help_for_screen(book, "chat").help_id == "help-chat"
    assert help_for_screen(book, "review") is None


# ---------------------------------------------------------------------
# The held doc: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_doc_record_round_trips():
    doc = _doc()
    assert validate_doc(doc) is doc
    rebuilt = build_doc(_stored_doc(doc))
    assert rebuilt == doc
    assert rebuilt.item_id == "doc-test"
    assert rebuilt.keywords == ("provider", "key")
    record = doc_record(doc)
    assert record["type"] == "help_doc"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_doc_refuses_stored_judgements():
    for key in ("answer", "answered", "gaps", "segment", "verdict",
                "coverage", "matched"):
        fields = _stored_doc(_doc())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_doc(fields)
    fields = _stored_doc(_doc())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_doc(fields)


def test_doc_refuses_a_live_answer_road():
    for key in ("live_search", "web_search", "network_lookup",
                "llm_answer", "model_answer"):
        fields = _stored_doc(_doc())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_doc(fields)
        assert "local docs" in str(caught.value)
    for key in ("live_search", "model_answer"):
        fields = _help().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_screen_help(fields)
        assert "local docs" in str(caught.value)
    entry = _help(screen="CHAT")
    assert validate_screen_help(entry) is entry
    assert entry.screen == "chat"
    assert screen_record(entry)["type"] == "help_screen"


def test_doc_vocabularies_are_closed():
    assert _doc(standing="STALE").standing == "stale"
    with pytest.raises(ValueError):
        _doc(standing="guessed")
    with pytest.raises(ValueError):
        _doc(topic="a hunch")
    with pytest.raises(ValueError):
        _doc(title="   ")
    with pytest.raises(ValueError):
        _doc(seq=0)
    with pytest.raises(ValueError):
        _doc(keywords="provider")


def test_plain_telling_derives_from_the_docs_own_fields():
    doc = _doc(
        title="Test Doc", topic="editing and undo",
        standing="stale",
        detail="The list waits on a sandbox refresh.")
    lines = plain_lines(doc)
    assert lines[0] == "Doc: Test Doc"
    assert lines[1] == "Topic: editing and undo"
    assert lines[2] == "Standing: stale"
    assert plain_words(doc) == doc_plain_words(doc)
    assert "Test Doc" in plain_words(doc)
    assert "sandbox refresh" in plain_words(doc)


def test_stale_doc_stands_named_in_its_gaps():
    doc = _doc(standing="stale")
    assert doc_gaps(doc) == ("stale",)
    assert doc_passes(doc) is False
    text = format_doc(doc)
    assert "stands stale" in text
    current_text = format_doc(_doc())
    assert "stands current" in current_text


def test_view_and_screen_help_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "help_view"
    assert record["view_filter"] == "all"
    assert "shows all docs" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    entry = _help()
    assert build_screen_help(entry.to_record()) == entry
    assert "chat screen" in format_screen_help(entry)
    with pytest.raises(ValueError):
        _help(screen="the void")


# ---------------------------------------------------------------------
# The answer and the coverage: derived at call time, never held.
# ---------------------------------------------------------------------


def test_answer_is_derived_from_current_docs_alone():
    book = _mixed_book()
    answer = derive_answer(book, "how do I reach a provider key?")
    assert answer.answered is True
    assert answer.matched == ("doc-test",)
    assert answer.gaps == ()
    assert "A test doc held as data" in answer.lines[0]
    assert answer_record(answer)["type"] == "help_answer"
    assert answer_record(book, "provider key?")["answered"] is True
    assert "Answered from the local docs" in answer_plain_words(answer)
    text = format_answer(book, "provider key?")
    assert "no live search" in text


def test_question_matching_only_a_stale_doc_stands_unanswered():
    book = _mixed_book()
    answer = derive_answer(book, "which sandbox command is allowed?")
    assert answer.answered is False
    assert answer.matched == ()
    assert answer.stale_matched == ("doc-stale",)
    assert answer.gaps == ("stale doc",)
    assert "stands unanswered" in format_answer(answer)
    assert "stale doc" in format_answer(answer)


def test_question_with_no_local_doc_stands_honestly_unanswered():
    book = load_help_answers()
    answer = derive_answer(book, "how do I juggle flaming torches?")
    assert answer.answered is False
    assert answer.gaps == ("no local doc",)
    assert "Unanswered" in answer_plain_words(answer)
    example = derive_answer(book, EXAMPLE_QUESTION)
    assert example.answered is True
    assert example.matched == ("doc-undo-commit",)
    with pytest.raises(ValueError):
        derive_answer(book, "   ")


def test_screen_help_and_coverage_are_derived():
    book = _book(helps=[_help(), _help(
        help_id="help-two", seq=2, screen="editor",
        title="The editor")])
    assert help_for_screen(book, "chat").help_id == "help-test"
    assert help_for_screen(book, "EDITOR").help_id == "help-two"
    assert help_for_screen(book, "review") is None
    coverage = derive_coverage(book)
    assert coverage.covered == ("chat", "editor")
    assert "review" in coverage.uncovered
    assert coverage_record(book)["type"] == "help_coverage"
    assert "uncovered" in coverage_plain_words(book)
    assert "No held help stands for the review screen" in format_screen(
        book, "review")
    assert "chat screen" in format_screen(book, "chat")
    assert "Screen help coverage" in format_coverage(book)
    with pytest.raises(ValueError):
        help_for_screen(book, "the void")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, HelpPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.docs[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.docs[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "help_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_docs():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, HelpVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "help_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(docs=[_doc()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(docs=[_doc(standing="stale")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        docs=[_doc(standing="stale")],
        views=[_view(view_filter="current")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_standing_readings():
    book = _mixed_book()
    assert [d.doc_id for d in shown_docs(book)] == [
        "doc-test", "doc-stale"]
    current_view = _view(view_id="view-c", seq=2, view_filter="current")
    book2 = _book(
        docs=[_doc(), _doc(
            doc_id="doc-stale", seq=2,
            title="Commands the sandbox allows",
            topic="sandbox and safety", standing="stale")],
        views=[_view(), current_view])
    assert [d.doc_id for d in shown_docs(book2, current_view)] == [
        "doc-test"]
    assert [d.doc_id for d in docs_for_standing(book2, "stale")] == [
        "doc-stale"]
    assert [d.doc_id for d in passing_docs(book2)] == ["doc-test"]
    assert total_docs(book2) == 2
    with pytest.raises(ValueError):
        docs_for_standing(book2, "maybe")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(docs=[_doc(), _doc(seq=2)])
    with pytest.raises(ValueError):
        _book(docs=[_doc(), _doc(doc_id="doc-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="current")])
    with pytest.raises(ValueError):
        _book(helps=[_help(), _help(screen="editor")])
    with pytest.raises(ValueError) as caught:
        _book(helps=[_help(), _help(help_id="help-two", seq=2)])
    assert "one help entry stands per screen" in str(caught.value)
    fields = {
        "schema": HELP_ANSWERS_SCHEMA, "slice": "M-186",
        "guide": {"title": "A test help book"},
        "docs": [_stored_doc(_doc())],
        "views": [_stored_view(_view())], "helps": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    fields["verdict"] = None
    del fields["verdict"]
    fields["answer"] = "invented"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": HELP_ANSWERS_SCHEMA, "slice": "M-186",
        "guide": {"title": "A test help book"},
        "docs": [], "views": [], "helps": [], "panels": [],
        "live_search": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "live answer road" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / HELP_ANSWERS_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "help_answers.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_help_answers_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_docs(book) == 6


def test_registry_holds_docs_and_views_one_by_one():
    registry = HelpRegistry()
    assert registry.list_items() == ()
    held = registry.register_doc(_doc())
    assert held.doc_id == "doc-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["doc-test", "view-test"]
    assert registry.get_doc("doc-test").title == "A test doc"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld help book"
    with pytest.raises(ValueError):
        registry.register_doc(_doc(seq=2))
    with pytest.raises(ValueError):
        registry.register_doc(_doc(doc_id="doc-two"))
    with pytest.raises(KeyError):
        registry.get_doc("doc-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = HelpRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test help book"
    assert len(registry.list_docs()) == 2
    other = _book(docs=[_doc(doc_id="doc-x", seq=9, title="Other")],
                  views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "in topic 'providers and keys'" in format_book(book)
    assert "doc-stale" in format_book(book, "stale")
    assert "doc-test" not in format_book(book, "stale")
    assert "Help panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith("The help book holds 2 docs")
    screen = format_help_answers_screen(book)
    assert "Help That Answers (M-186)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "uncovered" in screen
    record = book_record(book)
    assert record["type"] == "help_book"
    assert record["title"] == "A test help book"
    assert len(record["docs"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "doc-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    doc_text = format_doc(book.docs[0])
    assert "Doc: A test doc" in doc_text
    assert "Standing: current" in doc_text


def test_parse_args_inspect_and_loader_roads():
    assert parse_help_args("") == ("show", None)
    assert parse_help_args("show") == ("show", None)
    assert parse_help_args(None) == ("show", None)
    assert parse_help_args("doc doc-test") == ("doc", "doc-test")
    assert parse_help_args("ask how do I undo a commit?") == (
        "ask", "how do I undo a commit?")
    assert parse_help_args("screen command palace") == (
        "screen", "command palace")
    assert parse_help_args("view view-test") == ("view", "view-test")
    assert parse_help_args("standing stale") == ("standing", "stale")
    assert parse_help_args("panel") == ("panel", None)
    assert parse_help_args("verdict") == ("verdict", None)
    assert parse_help_args("coverage") == ("coverage", None)
    for bad in ("dance", "doc", "ask", "screen", "panel now",
                "standing a b"):
        with pytest.raises(ValueError):
            parse_help_args(bad)
    doc = _doc()
    assert inspect_help_source(doc) == {"kind": "doc", "doc_id": "doc-test"}
    assert inspect_help_source(_stored_doc(doc))["kind"] == "doc"
    assert inspect_help_source(_stored_view(_view()))["kind"] == "view"
    assert inspect_help_source(_help().to_record())["kind"] == "help"
    assert inspect_help_source(42)["kind"] == "unknown"
    book = load_help_answers({
        "schema": HELP_ANSWERS_SCHEMA, "slice": "M-186",
        "guide": {"title": "A judged book"},
        "docs": [_stored_doc(_doc())],
        "views": [_stored_view(_view())], "helps": [], "panels": []})
    assert isinstance(book, HelpBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_help_answers({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_help_answers({"slice": "M-999"})
    built = build_doc(
        doc_id="doc-kw", seq=3, title="Kw Doc",
        topic="plain language", standing="current",
        detail="Built by fields.", keywords=["plain"],
        recorded_on=ON, actor=BY,
        source="test source", origin_session="session-test")
    assert built.doc_id == "doc-kw"
    assert doc_passes(built) is True


# ---------------------------------------------------------------------
# M-186 agent layer: the agent holds a help book
# for the session, docs and views are published
# as session news through the checkpoint road
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the
# coverage is derived from the book's held screen
# helps, and every answer is derived at call time
# from the held docs alone - a question no current
# doc answers stands unanswered. This layer calls
# no model, searches nothing live, opens no
# network and persists nothing beyond the session
# journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _help_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_help_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / HELP_ANSWERS_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "help_answers.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestHelpAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.help_answers_status()
        assert status["docs"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["help"]["title"] == EXAMPLE_TITLE
        assert len(status["help"]["docs"]) == 6
        assert len(status["help"]["views"]) == 2
        assert len(status["help"]["helps"]) == 4
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m185-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert status["coverage"]["uncovered"] == [
            "review", "settings", "onboarding", "command palace"]
        assert status["example_answer"]["answered"] is True
        assert status["example_answer"]["matched"] == ["doc-undo-commit"]
        assert "local docs held on this machine alone" in status["rule"]
        assert "Plain words, Jarl mode" in status["plain_words"]
        assert "Help That Answers (M-186)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._help_answers_registry()
        assert agent._help_answers_registry() is first
        assert agent._help_answers_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.help_answers_status()
        assert agent.get_help_doc("doc-undo-commit").title == (
            "Undo a commit")
        assert agent.get_help_view("view-all").view_filter == "all"
        assert agent.get_screen_help("chat").help_id == "help-chat"
        assert [d.doc_id for d in agent.help_answers_with_standing(
            "stale")] == ["doc-sandbox-commands"]
        assert [d.doc_id for d in agent.help_answers_passing()] == [
            "doc-undo-commit", "doc-first-task", "doc-provider-keys",
            "doc-crew-dealing", "doc-plain-words"]
        agent.help_answers_panel()
        agent.help_answers_verdict()
        agent.ask_help(EXAMPLE_QUESTION)
        agent.report_help_answers()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("help")] == []
        with pytest.raises(KeyError):
            agent.get_help_doc("doc-nope")
        with pytest.raises(KeyError):
            agent.get_help_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_screen_help("review")
        with pytest.raises(ValueError):
            agent.help_answers_with_standing("maybe")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_help_doc(_doc())
        status = agent.help_answers_status()
        assert [d["doc_id"] for d in status["docs"]] == ["doc-test"]
        assert status["book"]["title"] == "An unheld help book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert status["coverage"]["covered"] == []
        assert "doc-test" in status["screen"]

    def test_held_doc_never_falls_back_to_the_example(
            self, agent):
        agent.register_help_doc(_doc())
        with pytest.raises(KeyError):
            agent.get_help_doc("doc-undo-commit")
        with pytest.raises(KeyError):
            agent.get_help_view("view-all")
        doc = agent.get_help_doc("doc-test")
        assert doc.title == "A test doc"
        assert agent.help_answers_book().title == "An unheld help book"

    def test_screen_helps_and_coverage_stand_in_the_example(self, agent):
        with pytest.raises(KeyError):
            agent.get_screen_help("command palace")
        chat = agent.get_screen_help("chat")
        assert chat.help_id == "help-chat"
        assert chat.screen == "chat"
        status = agent.help_answers_status()
        assert status["coverage"]["covered"] == [
            "chat", "terminal", "editor", "lessons"]


class TestHelpAgentHolding:
    def test_register_doc_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_help_doc(_doc())
        assert result["doc"]["doc_id"] == "doc-test"
        assert result["record_news"]["type"] == "help_doc"
        assert "doc-test" in result["screen"]
        events = _help_events(store, session_id, "help_doc")
        assert len(events) == 1
        agent.close()

    def test_duplicate_doc_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_help_doc(_doc())
        with pytest.raises(ValueError):
            agent.register_help_doc(_doc(seq=9))
        events = _help_events(store, session_id, "help_doc")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_help_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_help_events(store, session_id, "help_view")) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_help_doc(_doc())
        result = agent.view_help("current")
        assert result["view"]["view_filter"] == "current"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "help_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_help_events(store, session_id, "help_view")) == 1
        assert len(_help_events(store, session_id, "help_panel")) == 1
        assert len(_help_events(store, session_id, "help_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_help_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "help_doc", "help_view"]
        assert len(_help_events(store, session_id, "help_doc")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_help_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "help_panel"
        assert result["coverage_record"]["uncovered"] == [
            "review", "settings", "onboarding", "command palace"]
        with pytest.raises(ValueError):
            agent.record_help_book()
        assert len(_help_events(store, session_id, "help_doc")) == 6
        assert len(_help_events(store, session_id, "help_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_help_book_file(tmp_path)
        book = load_help_answers_file(path)
        result = agent.record_help_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_help_answers()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["example_answer"]["answered"] is True
        assert "doc-undo-commit" in report["book_text"]
        assert "Undo a commit" in report["answer_text"]
        agent.register_help_doc(_doc())
        report = agent.report_help_answers()
        assert report["book"]["title"] == "An unheld help book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestHelpTerminalSurface:
    def test_show_doc_ask_screen_view_standing_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/helpask")
        assert "Help That Answers (M-186)" in text
        _, _, text = _slash(agent, "/helpask doc doc-undo-commit")
        assert "Doc: Undo a commit" in text
        _, _, text = _slash(agent, "/helpask ask how do I undo a commit?")
        assert "Undo a commit" in text
        assert "local docs" in text
        _, _, text = _slash(agent, "/helpask screen chat")
        assert "chat screen" in text
        _, _, text = _slash(agent, "/helpask screen review")
        assert "stands uncovered" in text
        _, _, text = _slash(agent, "/helpask view view-all")
        assert "filter all" in text
        _, _, text = _slash(agent, "/helpask standing stale")
        assert "doc-sandbox-commands" in text
        assert "doc-undo-commit" not in text
        _, _, text = _slash(agent, "/helpask panel")
        assert "Help panel under view view-all" in text
        _, _, text = _slash(agent, "/helpask verdict")
        assert "strained" in text
        _, _, text = _slash(agent, "/helpask coverage")
        assert "uncovered" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/helpask [show|doc <doc-id>"
                "|ask <words>|screen <screen>|view <view-id>"
                "|standing <standing>|panel|verdict|coverage]") in text
        _, _, text = _slash(agent, "/helpask dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/helpask doc doc-nope")
        assert "no doc named" in text


@pytest.fixture()
def helpask_handler(agent, monkeypatch):
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


def _helpask_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestHelpCommand:
    def test_show_is_default(self, helpask_handler, agent):
        helpask_handler._handle_helpask("")
        assert "Help That Answers (M-186)" in (
            _helpask_published_text(helpask_handler))

    def test_doc_ask_screen_view_standing_panel_verdict(
            self, helpask_handler, agent):
        helpask_handler._handle_helpask("doc doc-undo-commit")
        assert "Doc: Undo a commit" in _helpask_published_text(
            helpask_handler)
        helpask_handler._handle_helpask("ask how do I undo a commit?")
        assert "Undo a commit" in _helpask_published_text(helpask_handler)
        helpask_handler._handle_helpask("screen chat")
        assert "chat screen" in _helpask_published_text(helpask_handler)
        helpask_handler._handle_helpask("view view-all")
        assert "filter all" in _helpask_published_text(helpask_handler)
        helpask_handler._handle_helpask("standing stale")
        assert "doc-sandbox-commands" in _helpask_published_text(
            helpask_handler)
        helpask_handler._handle_helpask("panel")
        assert "Help panel under view" in _helpask_published_text(
            helpask_handler)
        helpask_handler._handle_helpask("verdict")
        assert "strained" in _helpask_published_text(helpask_handler)

    def test_bad_grammar_is_published(
            self, helpask_handler, agent):
        helpask_handler._handle_helpask("dance party")
        assert USAGE in _helpask_published_text(helpask_handler)
        helpask_handler._handle_helpask("doc doc-nope")
        assert "no doc named" in _helpask_published_text(helpask_handler)


class TestChatScreenRoutingHelp:
    def test_onboard_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/helpask panel", _FakeLog())
        assert calls == [("/helpask", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/helpask[/green] - show help that answers (M-186)" in (
            text)
        assert ('"/helpask": "Usage: /helpask | '
                '/helpask doc <doc-id>') in text


class TestHelpDerivedRoads:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.help_answers_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-all"
        verdict = agent.help_answers_verdict()
        assert verdict.verdict == "strained"
        found = agent.help_answers_verdict("view-current")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_help_doc(_doc())
        with pytest.raises(ValueError):
            agent.help_answers_panel()
        with pytest.raises(ValueError):
            agent.help_answers_verdict()

    def test_view_road_over_an_unshown_filter_is_shut(self, agent):
        agent.register_help_doc(_doc(standing="stale"))
        result = agent.view_help("current")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_ask_road_answers_and_stands_unanswered_honestly(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.ask_help("how do I undo a commit?")
        assert result["answer"]["answered"] is True
        assert result["answer"]["matched"] == ["doc-undo-commit"]
        assert "Undo a commit" in result["answer_text"]
        stale = agent.ask_help("which sandbox command is allowed?")
        assert stale["answer"]["answered"] is False
        assert stale["answer"]["gaps"] == ["stale doc"]
        none = agent.ask_help("how do I juggle flaming torches?")
        assert none["answer"]["answered"] is False
        assert none["answer"]["gaps"] == ["no local doc"]
        doc = agent.get_help_doc("doc-sandbox-commands")
        assert doc_gaps(doc) == ("stale",)
        assert doc_passes(doc) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("help")] == []
        agent.close()
