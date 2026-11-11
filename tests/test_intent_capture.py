"""M-202 Intent Capture (PROJECT_FORGE form) - pure-layer tests.

TIER: integration

The pure layer is the intent, held as data: one
record per intent, held whole - the project it
opens, and what, why and success in the user's
plain words, stored VERBATIM, the exact strings
the user gave, never stripped, normalised or
rewritten - and the citation the coder's plan
carries, held as data beside it. The citation
check is derived at call time from the stored
words alone: a plan carrying no citation stands
uncited, named in its gaps, and a plan citing
words that stand in none of the stored what, why
or success stands uncited too, named in its gaps
beside it; the field a standing citation cites
is derived and told, never stored. The notes are
held as data beside the book, each naming its
intent, its stance and its target, and the intent
index is derived at call time from the held
intents alone, never stored where it could drift.
Two intents standing for one intent id refuse by
name, and one stance record stands per intent
stance. A record claiming a project was actually
opened, a plan actually run or executed live, or
a push actually made refuses by name, and a stored
index, verdict, board or current intent refuses
by name. The shipped example book is held in a
data file, and a loader reads a book from any
file. No charter row names this slice: the M-171
TUI charter binds Part VIII alone, and the M-005
method charter names no slice row - its source
note names the whole Part IX range M-201-M-232 as
the part that executes it, and the tests pin both
facts live. This layer opens no project, runs no
plan, executes nothing, pushes nothing and opens
no network: it holds intents as data and tells
them.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.intent_capture import (
    CITATION_FIELDS,
    CITING_WORDS,
    EXAMPLE_CITATION,
    INDEX_ACTION,
    INTENT_RESOURCE,
    INTENT_RULE,
    INTENT_SCHEMA,
    INTENT_SLICE,
    PLAIN_EXPLANATION,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    IndexEntry,
    IntentBook,
    IntentIndex,
    IntentPanel,
    IntentRecord,
    IntentRegistry,
    IntentVerdict,
    IntentView,
    NoteRecord,
    board_record,
    book_record,
    build_book,
    build_intent,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    citation_field,
    current_intent,
    derive_index,
    derive_panel,
    derive_verdict,
    first_note,
    format_book,
    format_citation,
    format_index,
    format_intent,
    format_intent_screen,
    format_note,
    format_panel,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    intent_cites,
    intent_for_citation,
    intent_gaps,
    intent_record,
    intents_for_project,
    load_intents,
    load_intents_file,
    normalize_stance,
    normalize_view_filter,
    note_for_intent,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_intent_args,
    passing_intents,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    shown_intents,
    validate_book,
    validate_intent,
    validate_note,
    validate_panel,
    validate_row,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.method_charter import (
    load_charter as load_method_charter,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-10"
BY = "the coordinator"
EXAMPLE_TITLE = "Intent capture at the M-201 slice boundary"
EXAMPLE_CITATIONS = [
    "my own words for what, why and success",
    "word for word as I gave it",
]
EXAMPLE_INTENT_IDS = (
    "intent-plain-words", "intent-verbatim",
    "intent-drifting-plan", "intent-unplanned")


def _intent(**overrides):
    fields = {
        "intent_id": "intent-test",
        "seq": 1,
        "project": "A test project",
        "what": "I want a test intent held as data",
        "why": "because the tests must cite it",
        "success": "the test intent stands cited",
        "citation": "a test intent held as data",
        "detail": "A test intent held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "intent-test",
    }
    fields.update(overrides)
    return build_intent(fields)


def _stored_intent(intent):
    return intent.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "intent-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "intent_id": "intent-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "intent-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(intents=None, views=None, notes=None, **overrides):
    fields = {
        "schema": INTENT_SCHEMA,
        "slice": "M-202",
        "intent_capture": {"title": "A test intent book"},
        "intents": [_stored_intent(item) for item in (
            intents if intents is not None else [_intent()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(intents=[
        _intent(),
        _intent(intent_id="intent-hidden", seq=2,
                project="A hidden project",
                citation=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_intents()
    assert book.title == EXAMPLE_TITLE
    assert book.intent_ids() == EXAMPLE_INTENT_IDS
    assert [v.view_id for v in book.views] == [
        "view-intent", "view-citing"]
    assert [m.intent_id for m in book.notes] == [
        "intent-plain-words", "intent-drifting-plan"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m201-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.intent_ids())
    derived = derive_panel(book, "view-intent")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 4
    assert panel.total_shown == derived.total_shown == 4
    assert {c.standing: c.items for c in panel.target_counts} == {
        "citing": 2, "uncited": 2}
    assert derive_verdict(book, "view-intent").verdict == "strained"
    assert derive_verdict(book, "view-intent").passing_shown == 2
    assert derive_verdict(book, "view-citing").verdict == "open"
    assert derive_verdict(book, "view-citing").passing_shown == 2
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / INTENT_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == INTENT_SCHEMA
    assert raw["slice"] == "M-202"
    assert "verdict" not in raw
    assert "intent_index" not in raw
    assert "board" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-202")]
    assert slice_.title == "Intent capture (PROJECT_FORGE form)"
    assert slice_.part == 9
    assert "what/why/success" in slice_.summary
    assert "stored verbatim" in slice_.summary
    assert "must cite it" in slice_.summary
    assert INTENT_SLICE == "M-202"


def test_charter_rows_do_not_name_m202():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-202" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "PROJECT_FORGE" in method.source_note


def test_closed_vocabularies():
    assert CITING_WORDS == ("citing", "uncited")
    assert CITATION_FIELDS == ("what", "why", "success")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "citing", "uncited")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CITATION == (
        "my own words for what, why and success")
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in INTENT_RULE
    assert "stored verbatim" in INTENT_RULE
    assert "M-202" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /intent")


def test_shipped_book_judged_honestly_as_data():
    book = load_intents()
    opening = book.intent_for("intent-plain-words")
    assert intent_cites(opening) is True
    assert intent_gaps(opening) == ()
    assert citation_field(opening) == "what"
    assert plain_lines(opening) == (
        "Intent: Mythic Agent Coder",
        "What: I want a coder that opens every new project with "
        "my own words for what, why and success",
        "Why: because plans drift when they start from the "
        "coder's words instead of mine",
        "Success: a new project opens with my words stored "
        "verbatim and every plan cites them",
        "Citation: my own words for what, why and success")
    verbatim = book.intent_for("intent-verbatim")
    assert citation_field(verbatim) == "success"
    drifting = book.intent_for("intent-drifting-plan")
    assert intent_gaps(drifting) == (
        "the plan cites words not in the stored intent",)
    assert intent_cites(drifting) is False
    unplanned = book.intent_for("intent-unplanned")
    assert unplanned.citation == ""
    assert intent_gaps(unplanned) == ("the plan cites no intent",)
    assert [g.intent_id for g in passing_intents(book)] == [
        "intent-plain-words", "intent-verbatim"]
    index = derive_index(book)
    assert [e.citation for e in index.entries] == EXAMPLE_CITATIONS
    assert index.gaps == ("intent-drifting-plan", "intent-unplanned")
    assert intent_for_citation(book, EXAMPLE_CITATION).intent_id == (
        "intent-plain-words")
    assert intent_for_citation(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-open"
    assert note_for_intent(
        book, "intent-plain-words", "note").note_id == (
            "note-note-open")
    assert note_for_intent(book, "intent-nope") is None
    assert current_intent(book).intent_id == "intent-drifting-plan"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "citing", "intents": 2},
        {"standing": "uncited", "intents": 2}]
    assert board["total"] == 4
    assert board["current_intent"] == "intent-drifting-plan"
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["next_slice"] == "M-227"
    assert citizen["m202_title"] == "Intent capture (PROJECT_FORGE form)"
    assert citizen["m202_part"] == 9
    assert citizen["m202_status"] == "done"


# ---------------------------------------------------------------------
# The held intent: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_intent_record_round_trips():
    intent = _intent()
    assert validate_intent(intent) is intent
    rebuilt = build_intent(_stored_intent(intent))
    assert rebuilt == intent
    assert rebuilt.item_id == "intent-test"
    assert rebuilt.citation == "a test intent held as data"
    record = intent_record(intent)
    assert record["type"] == "intent_record"
    assert record["cites"] is True
    assert record["gaps"] == []


def test_verbatim_words_stand_exactly_as_given():
    intent = _intent(
        what="  Keep  My Words, EXACTLY as I said them  ",
        citation="Keep  My Words, EXACTLY")
    assert intent.what == "  Keep  My Words, EXACTLY as I said them  "
    assert intent_cites(intent) is True
    assert citation_field(intent) == "what"
    assert "What:   Keep  My Words, EXACTLY as I said them  " in (
        plain_lines(intent))
    respaced = _intent(
        what="  Keep  My Words, EXACTLY as I said them  ",
        citation="Keep My Words, EXACTLY")
    assert intent_cites(respaced) is False
    assert intent_gaps(respaced) == (
        "the plan cites words not in the stored intent",)
    lowered = _intent(citation="A TEST INTENT HELD AS DATA")
    assert intent_cites(lowered) is False


def test_intent_refuses_stored_judgements():
    for key in ("standing", "cites", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_intent",
                "board", "citation_field"):
        fields = _stored_intent(_intent())
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_intent(fields)
    fields = _stored_intent(_intent())
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_intent(fields)


def test_intent_refuses_a_live_claim():
    for key in ("opens_project", "runs_plan", "executes_plan",
                "pushes_intent", "posts_note", "opens_network"):
        fields = _stored_intent(_intent())
        fields[key] = True
        with pytest.raises(ValueError):
            build_intent(fields)


def test_intent_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _intent(what="")
    with pytest.raises(ValueError):
        _intent(what="   ")
    with pytest.raises(ValueError):
        _intent(why=None)
    with pytest.raises(ValueError):
        _intent(success=42)
    with pytest.raises(ValueError):
        _intent(citation=42)
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    intent = _intent(citation=None)
    assert intent.citation == ""
    assert intent_gaps(intent) == ("the plan cites no intent",)


def test_plain_telling_derives_from_the_intents_own_fields():
    intent = _intent()
    assert plain_lines(intent) == (
        "Intent: A test project",
        "What: I want a test intent held as data",
        "Why: because the tests must cite it",
        "Success: the test intent stands cited",
        "Citation: a test intent held as data")
    segment = segment_of(intent)
    assert segment.startswith("intent-test: A test project")
    assert "cited in: 'what'" in segment
    assert "gaps: none" in segment
    assert plain_words(intent).startswith(
        "A test project - what I want a test intent held as data")


def test_uncited_intents_stand_named_in_their_gaps():
    silent = _intent(citation="")
    assert intent_gaps(silent) == ("the plan cites no intent",)
    assert citation_field(silent) is None
    assert "Citation: none" in plain_lines(silent)
    foreign = _intent(citation="words the user never said")
    assert intent_gaps(foreign) == (
        "the plan cites words not in the stored intent",)
    assert citation_field(foreign) is None
    why_citer = _intent(citation="the tests must cite it")
    assert citation_field(why_citer) == "why"
    assert intent_cites(why_citer) is True


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "intent_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "intent_note"
    assert record["intent_id"] == "intent-test"
    assert view_plain_words(view) == "View view-test: shows all intents."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_intents_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.citation for e in index.entries] == [
        "a test intent held as data"]
    assert index.entries[0] == IndexEntry(
        citation="a test intent held as data",
        intent_id="intent-test", project="A test project")
    assert index.gaps == ("intent-hidden",)
    record = index_record(book)
    assert record["type"] == "intent_index"
    assert record["gaps"] == ["intent-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "intent_book"


def test_citation_target_reaches_its_intent_and_an_unheld_target_reaches_nothing():
    book = load_intents()
    assert intent_for_citation(
        book, "word for word as I gave it").intent_id == (
            "intent-verbatim")
    assert intent_for_citation(book, "") is None
    assert intent_for_citation(book, "not held at all") is None
    text = format_citation(book, "not held at all")
    assert "reaches nothing in this book" in text


def test_first_note_is_held_as_data():
    book = load_intents()
    first = first_note(book)
    assert first.note_id == "note-note-open"
    assert first.stance == "note"
    text = format_note(first)
    assert "Intent note note intent-plain-words" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").intent_id == "intent-test"
    assert note_for_intent(book, "intent-test").note_id == "note-test"
    assert note_for_intent(book, "intent-test", "praise") is None
    with pytest.raises(KeyError):
        book.note_for("note-nope")
    with pytest.raises(ValueError):
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.panel_id == "panel-view-test"
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert {c.standing: c.items for c in panel.target_counts} == {
        "citing": 1, "uncited": 1}
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book) == panel
    row = build_row(None, _intent())
    assert row.standing == "citing"
    assert validate_row(row, _intent()) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_intents():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "strained"
    assert verdict.passing_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "intent_verdict"
    citing_book = _book(views=[_view(view_filter="citing")])
    assert derive_verdict(citing_book).verdict == "open"
    empty_book = _book(intents=[_intent(citation="")],
                       views=[_view(view_filter="citing")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "shut"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict( IntentVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            passing_shown=1, latest_on=ON))


def test_shown_and_project_readings():
    book = load_intents()
    assert [g.intent_id for g in shown_intents(book)] == list(
        EXAMPLE_INTENT_IDS)
    assert [g.intent_id for g in shown_intents(book, "view-citing")] == [
        "intent-plain-words", "intent-verbatim"]
    assert [g.intent_id for g in intents_for_project(
        book, "The verbatim shelf")] == ["intent-verbatim"]
    assert intents_for_project(book, "No such project") == ()
    assert current_intent(_book()).intent_id if False else True
    assert current_intent(_mixed_book()).intent_id == "intent-hidden"
    assert current_intent(_book()) is None


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(intents=[_intent(), _intent(seq=2)])
    with pytest.raises(ValueError):
        _book(intents=[_intent(), _intent(intent_id="intent-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    fields = {
        "schema": INTENT_SCHEMA, "slice": "M-202",
        "intent_capture": {"title": "A judged book"},
        "intents": [_stored_intent(_intent())],
        "views": [_stored_view(_view())], "notes": [], "panels": [],
        "verdict": "open"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_intent"] = "intent-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_intent")
    fields["opens_project"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / INTENT_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "intent_capture.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_intents_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.intent_ids() == EXAMPLE_INTENT_IDS


def test_registry_holds_intents_and_views_one_by_one():
    registry = IntentRegistry()
    assert registry.title() is None
    registry.register_intent(_intent())
    registry.register_view(_view())
    assert [g.intent_id for g in registry.list_intents()] == ["intent-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_intent("intent-test").project == "A test project"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("intent-test").intent_id == "intent-test"
    with pytest.raises(ValueError):
        registry.register_intent(_intent(seq=9))
    with pytest.raises(ValueError):
        registry.register_intent(_intent(intent_id="intent-two"))
    with pytest.raises(KeyError):
        registry.get_intent("intent-nope")
    assert registry.book().title == "An unheld intent book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = IntentRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test intent book"
    assert registry.title() == "A test intent book"
    assert len(registry.list_intents()) == 2
    other = IntentRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    intent = _intent()
    assert "A test project" in plain_words(intent)
    assert panel_plain_words(_mixed_book()).startswith(
        "The intent book holds 2 intents")
    assert verdict_plain_words(_mixed_book()) == (
        "The intents stand strained: 1 of 2 shown intents stand citing.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 citing plans for 1 intents; uncited, "
        "named in its gaps: intent-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_intent(intent)
    assert "Intent: A test project" in text
    assert "stands cited" in text
    text = format_intent(_intent(citation=""))
    assert "stands uncited" in text
    assert "the plan cites no intent" in text
    book_text = format_book(_mixed_book())
    assert "Intent Capture (M-202) - A test intent book" in book_text
    assert "intent-hidden" in format_book(_mixed_book(), "A hidden project")
    assert "intent-test" not in format_book(_mixed_book(), "A hidden project")
    assert "Intent panel under view view-test" in format_panel(_mixed_book())
    assert "strained" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "a test intent held as data - A test project (intent-test)" in index_text
    assert "intent-hidden" in index_text
    screen = format_intent_screen()
    assert "Intent Capture (M-202)" in screen
    assert "intent-drifting-plan" in screen


def test_parse_args_board_and_loader_targets():
    assert parse_intent_args("") == ("show", None)
    assert parse_intent_args(None) == ("show", None)
    assert parse_intent_args("show") == ("show", None)
    assert parse_intent_args("intent intent-test") == (
        "intent", "intent-test")
    assert parse_intent_args("citation a test intent held as data") == (
        "citation", "a test intent held as data")
    assert parse_intent_args("project A test project") == (
        "project", "A test project")
    assert parse_intent_args("view view-test") == ("view", "view-test")
    assert parse_intent_args("note note-test") == ("note", "note-test")
    assert parse_intent_args("index") == ("index", None)
    assert parse_intent_args("panel") == ("panel", None)
    assert parse_intent_args("verdict") == ("verdict", None)
    for bad in ("dance", "intent", "citation", "project", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_intent_args(bad)
    board = board_record()
    assert board["type"] == "intent_board"
    assert board["total"] == 4
    assert board["current_intent"] == "intent-drifting-plan"
    book = load_intents({
        "schema": INTENT_SCHEMA, "slice": "M-202",
        "intent_capture": {"title": "A judged book"},
        "intents": [_stored_intent(_intent())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, IntentBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_intents({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_intents({"slice": "M-999"})
    built = build_intent(
        intent_id="intent-kw", seq=3, project="Kw Project",
        what="I want a kw intent", why="because kwargs build it",
        success="the kw intent stands cited",
        citation="a kw intent", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="intent-test")
    assert built.intent_id == "intent-kw"
    assert intent_cites(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-202 agent layer: the agent holds an intent
# book for the session, intents and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# shape), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held intents, the board is derived from
# the held citations, the roadmap standing is read
# from the shipped roadmap itself, and the stance
# targets are held as data beside them - holding
# one opens no project. This layer runs nothing,
# plans nothing, pushes nothing and persists
# nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_INTENT_EVENT_TYPES = (
    "intent_record", "intent_view", "intent_panel", "intent_verdict")


def _intent_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_intent_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / INTENT_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "intent_capture.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestIntentAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.intent_status()
        assert status["intents"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["intent_book"]["title"] == EXAMPLE_TITLE
        assert len(status["intent_book"]["intents"]) == 4
        assert len(status["intent_book"]["views"]) == 2
        assert len(status["intent_book"]["notes"]) == 2
        assert status["panel"]["total_items"] == 4
        assert status["panel"]["total_shown"] == 4
        assert status["panels"][0]["panel_id"] == "panel-m201-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 2
        assert [e["citation"] for e in status["index"]["entries"]] == (
            EXAMPLE_CITATIONS)
        assert status["index"]["gaps"] == [
            "intent-drifting-plan", "intent-unplanned"]
        assert status["first_note"]["note_id"] == "note-note-open"
        assert status["board"]["total"] == 4
        assert status["board"]["current_intent"] == "intent-drifting-plan"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["next_slice"] == "M-227"
        assert "held as data alone" in status["rule"]
        assert "intent-drifting-plan" in status["plain_words"]
        assert "Intent Capture (M-202)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._intent_registry()
        assert agent._intent_registry() is first
        assert agent._intent_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.intent_status()
        assert agent.get_intent(
            "intent-plain-words").project == "Mythic Agent Coder"
        assert agent.get_intent_view(
            "view-intent").view_filter == "all"
        assert agent.get_intent_note(
            "note-note-open").note_id == "note-note-open"
        assert [a.intent_id for a in agent.intents_for_project(
            "The verbatim shelf")] == ["intent-verbatim"]
        assert [a.intent_id for a in agent.intents_citing()] == [
            "intent-plain-words", "intent-verbatim"]
        agent.intent_panel()
        agent.intent_verdict()
        agent.intent_index()
        agent.report_intent()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _INTENT_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_intent("intent-nope")
        with pytest.raises(KeyError):
            agent.get_intent_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_intent_note("note-nope")
        with pytest.raises(ValueError):
            agent.intents_for_project("")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_intent(_intent())
        status = agent.intent_status()
        assert [a["intent_id"] for a in status["intents"]] == ["intent-test"]
        assert status["book"]["title"] == "An unheld intent book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["citation"] for e in status["index"]["entries"]] == [
            "a test intent held as data"]
        assert status["first_note"] is None
        assert "intent-test" in status["screen"]

    def test_held_intent_never_falls_back_to_the_example(
            self, agent):
        agent.register_intent(_intent())
        with pytest.raises(KeyError):
            agent.get_intent("intent-plain-words")
        with pytest.raises(KeyError):
            agent.get_intent_view("view-intent")
        with pytest.raises(KeyError):
            agent.get_intent_note("note-note-open")
        intent = agent.get_intent("intent-test")
        assert intent.project == "A test project"
        assert agent.intent_book().title == (
            "An unheld intent book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_intent_note("note-note-open")
        assert first.note_id == "note-note-open"
        assert first.intent_id == "intent-plain-words"
        status = agent.intent_status()
        assert status["index"]["gaps"] == [
            "intent-drifting-plan", "intent-unplanned"]
        assert status["first_note"]["intent_id"] == (
            "intent-plain-words")
        assert status["first_note"]["stance"] == "note"


class TestIntentAgentHolding:
    def test_register_intent_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_intent(_intent())
        assert result["intent"]["intent_id"] == "intent-test"
        assert result["record_news"]["type"] == "intent_record"
        assert "intent-test" in result["screen"]
        events = _intent_events(store, session_id, "intent_record")
        assert len(events) == 1
        agent.close()

    def test_duplicate_intent_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_intent(_intent())
        with pytest.raises(ValueError):
            agent.register_intent(_intent(seq=9))
        with pytest.raises(ValueError):
            agent.register_intent(_intent(intent_id="intent-two"))
        events = _intent_events(store, session_id, "intent_record")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_intent_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_intent_events(
            store, session_id, "intent_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_intent(_intent())
        result = agent.view_intent("citing")
        assert result["view"]["view_filter"] == "citing"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "intent_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_intent_events(
            store, session_id, "intent_view")) == 1
        assert len(_intent_events(
            store, session_id, "intent_panel")) == 1
        assert len(_intent_events(
            store, session_id, "intent_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_intent_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "intent_record", "intent_view"]
        assert len(_intent_events(
            store, session_id, "intent_record")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_intent_book()
        assert result["count"] == 4
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "intent_panel"
        assert result["index_record"]["gaps"] == [
            "intent-drifting-plan", "intent-unplanned"]
        with pytest.raises(ValueError):
            agent.record_intent_book()
        assert len(_intent_events(
            store, session_id, "intent_record")) == 4
        assert len(_intent_events(
            store, session_id, "intent_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_intent_book_file(tmp_path)
        book = load_intents_file(path)
        result = agent.record_intent_book(book)
        assert result["count"] == 4
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_intent()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == [
            "intent-drifting-plan", "intent-unplanned"]
        assert "intent-plain-words" in report["book_text"]
        assert "my own words for what, why and success - Mythic Agent Coder (intent-plain-words)" in report["index_text"]
        agent.register_intent(_intent())
        report = agent.report_intent()
        assert report["book"]["title"] == "An unheld intent book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestIntentTerminalHeading:
    def test_show_intent_target_citation_project_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/intent")
        assert "Intent Capture (M-202)" in text
        _, _, text = _slash(agent, "/intent intent intent-plain-words")
        assert "Intent: Mythic Agent Coder" in text
        _, _, text = _slash(
            agent,
            "/intent citation my own words for what, why and success")
        assert "Intent: Mythic Agent Coder" in text
        _, _, text = _slash(agent, "/intent citation triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/intent project The verbatim shelf")
        assert "intent-verbatim" in text
        assert "intent-plain-words" not in text
        _, _, text = _slash(agent, "/intent view view-intent")
        assert "filter all" in text
        _, _, text = _slash(agent, "/intent note note-note-open")
        assert "Intent note note intent-plain-words" in text
        _, _, text = _slash(agent, "/intent index")
        assert "Intent index" in text
        assert "intent-unplanned" in text
        _, _, text = _slash(agent, "/intent panel")
        assert "Intent panel under view view-intent" in text
        _, _, text = _slash(agent, "/intent verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/intent [show|intent <intent-id>"
                "|citation <citation>|project <project>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/intent dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/intent intent intent-nope")
        assert "no intent named" in text


@pytest.fixture()
def intent_handler(agent, monkeypatch):
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


def _intent_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestIntentCommand:
    def test_show_is_default(self, intent_handler, agent):
        intent_handler._handle_intent("")
        assert "Intent Capture (M-202)" in (
            _intent_published_text(intent_handler))

    def test_intent_target_citation_project_view_note_index_panel_verdict(
            self, intent_handler, agent):
        intent_handler._handle_intent("intent intent-plain-words")
        assert "Intent: Mythic Agent Coder" in _intent_published_text(
            intent_handler)
        intent_handler._handle_intent(
            "citation my own words for what, why and success")
        assert "Intent: Mythic Agent Coder" in _intent_published_text(
            intent_handler)
        intent_handler._handle_intent("project The verbatim shelf")
        assert "intent-verbatim" in _intent_published_text(
            intent_handler)
        intent_handler._handle_intent("view view-intent")
        assert "filter all" in _intent_published_text(intent_handler)
        intent_handler._handle_intent("note note-note-open")
        assert "Intent note note intent-plain-words" in (
            _intent_published_text(intent_handler))
        intent_handler._handle_intent("index")
        assert "Intent index" in _intent_published_text(intent_handler)
        intent_handler._handle_intent("panel")
        assert "Intent panel under view" in _intent_published_text(
            intent_handler)
        intent_handler._handle_intent("verdict")
        assert "strained" in _intent_published_text(intent_handler)

    def test_bad_grammar_is_published(
            self, intent_handler, agent):
        intent_handler._handle_intent("dance party")
        assert USAGE in _intent_published_text(intent_handler)
        intent_handler._handle_intent("intent intent-nope")
        assert "no intent named" in _intent_published_text(
            intent_handler)


class TestChatScreenRoutingIntent:
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
        screen.handle_command("/intent panel", _FakeLog())
        assert calls == [("/intent", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/intent[/green] - show intent capture (M-202)" in (
            text)
        assert ('"/intent": "Usage: /intent | '
                '/intent intent <intent-id>') in text


class TestIntentDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.intent_panel()
        assert panel.total_shown == 4
        assert panel.panel_id == "panel-view-intent"
        verdict = agent.intent_verdict()
        assert verdict.verdict == "strained"
        found = agent.intent_verdict("view-citing")
        assert found.verdict == "open"
        assert found.passing_shown == 2
        agent.register_intent(_intent())
        with pytest.raises(ValueError):
            agent.intent_panel()
        with pytest.raises(ValueError):
            agent.intent_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_intent(_intent(citation=""))
        result = agent.view_intent("citing")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.intent_index()
        assert [e["citation"] for e in result["index"]["entries"]] == (
            EXAMPLE_CITATIONS)
        assert result["index"]["gaps"] == [
            "intent-drifting-plan", "intent-unplanned"]
        assert "my own words for what, why and success - Mythic Agent Coder (intent-plain-words)" in (
            result["index_text"])
        intent = agent.get_intent("intent-unplanned")
        assert intent_gaps(intent) == ("the plan cites no intent",)
        assert intent_cites(intent) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _INTENT_EVENT_TYPES] == []
        agent.close()
