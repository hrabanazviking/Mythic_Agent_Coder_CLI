"""M-190 Session Costs - pure-layer tests.

TIER: integration

The pure layer is the session costs, held as
data: one record per past session, held whole
as a browsable line - under its label, its
scope in the closed vocabulary, its cost and
its period held honestly (unknown stays
empty, never invented), the resume budget that
reaches it, named as data, and its detail - the
resume, fork and export budgets held as data
beside them, each naming its session, its
warning and its threshold, and the costs index
derived at call time from the held lines alone,
never stored where it could drift. A line
naming no resume budget stands unknown, named
in its gaps; two lines standing for one session
id refuse by name, and one warning record stands
per session budget. A record claiming a session
actually resumed, forked or exported refuses by
name, and a stored index or verdict refuses by
name. The panel is derived for one held view
and the verdict is derived for the whole book
under one view. The shipped example book is
held in a data file, and a loader reads a book
from any file. This layer resumes no session,
forks nothing, exports nothing and opens no
network: it holds the costs as data and
tells it.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.costs_face import (
    SCOPES,
    EXAMPLE_BUDGET,
    LEVELS,
    INDEX_ACTION,
    COSTS_FACE_RESOURCE,
    COSTS_FACE_SCHEMA,
    COSTS_FACE_SLICE,
    COSTS_RULE,
    GENTLE_WARNING_FRACTION,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    STANDING_WORDS,
    SpendLine,
    WarningRecord,
    CostsBook,
    CostsPanel,
    CostsFaceRegistry,
    CostsVerdict,
    CostsView,
    book_record,
    build_book,
    build_line,
    build_warning,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_index,
    derive_panel,
    derive_verdict,
    first_warning,
    format_book,
    format_line,
    format_index,
    format_warning,
    format_costs_screen,
    format_panel,
    format_budget,
    format_verdict,
    format_view,
    line_for_budget,
    line_gaps,
    line_counted,
    line_plain_words,
    line_record,
    lines_for_scope,
    index_plain_words,
    index_record,
    inspect_costs_source,
    warning_for_subject,
    warning_plain_words,
    warning_record,
    load_costs_face,
    load_costs_face_file,
    normalize_scope,
    normalize_level,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_costs_args,
    counted_lines,
    plain_lines,
    plain_words,
    shown_lines,
    total_lines,
    validate_book,
    validate_line,
    validate_warning,
    validate_panel,
    validate_row,
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
EXAMPLE_TITLE = "Costs face at the M-189 slice boundary"


def _line(**overrides):
    fields = {
        "line_id": "spend-test",
        "seq": 1,
        "label": "A test session",
        "scope": "session",
        "amount": "$0.10",
        "period": "12 minutes",
        "budget": "session-budget",
        "detail": "A test session held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "spend-test",
    }
    fields.update(overrides)
    return build_line(fields)


def _stored_line(line):
    return line.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "spend-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _warning(**overrides):
    fields = {
        "warning_id": "warning-test",
        "seq": 1,
        "subject": "spend-test",
        "level": "gentle",
        "threshold": "four fifths of the M-107 session budget",
        "title": "A test warning",
        "detail": "A test warning held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "spend-test",
    }
    fields.update(overrides)
    return build_warning(fields)


def _book(lines=None, views=None, warnings=None, **overrides):
    fields = {
        "schema": COSTS_FACE_SCHEMA,
        "slice": "M-190",
        "costs": {"title": "A test costs book"},
        "lines": [_stored_line(item) for item in (
            lines if lines is not None else [_line()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "warnings": [item.to_record() for item in (warnings or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(lines=[
        _line(),
        _line(line_id="spend-unknown", seq=2,
                 label="A stopped session", scope="slice",
                 amount="", period="", budget=""),
    ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_costs_face()
    assert book.title == EXAMPLE_TITLE
    assert book.line_ids() == (
        "spend-login-session", "spend-costs-face-slice",
        "spend-flaky-gate-session", "spend-gallery-slice",
        "spend-store-sweep", "spend-bank-wave-slice")
    assert [v.view_id for v in book.views] == [
        "view-all", "view-counted"]
    assert [w.subject for w in book.warnings] == [
        "session-login", "slice-m190"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m189-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.line_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.standing_counts} == {
        "counted": 5, "unknown": 1}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 5
    assert derive_verdict(book, "view-counted").verdict == "open"
    assert derive_verdict(book, "view-counted").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / COSTS_FACE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == COSTS_FACE_SCHEMA
    assert raw["slice"] == "M-190"
    assert "verdict" not in raw
    assert "costs_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-190")]
    assert slice_.title == "The costs face"
    assert slice_.part == 8
    assert "live spend per session and per slice" in slice_.summary
    assert "unknown = unknown" in slice_.summary
    assert "M-107" in slice_.summary
    assert COSTS_FACE_SLICE == "M-190"


def test_charter_does_not_name_m190():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert "M-190" not in owners


def test_closed_vocabularies():
    assert STANDING_WORDS == ("counted", "unknown")
    assert SCOPES == ("session", "slice")
    assert LEVELS == ("gentle", "near", "over")
    assert VIEW_FILTERS == ("all", "counted", "unknown")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_BUDGET == "session-budget"
    assert GENTLE_WARNING_FRACTION == 0.8
    assert normalize_scope("SESSION") == "session"
    assert normalize_level("NEAR") == "near"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_scope("the void")
    with pytest.raises(ValueError):
        normalize_level("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in COSTS_RULE
    assert "charges nothing" in COSTS_RULE
    assert "M-190" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /costs")


def test_shipped_book_judged_honestly_as_data():
    book = load_costs_face()
    login = book.line_for("spend-login-session")
    assert line_counted(login) is True
    assert line_gaps(login) == ()
    assert plain_lines(login) == (
        "Line: Fix the login redirect",
        "Scope: session",
        "Amount: $0.42",
        "Period: 18 minutes",
        "Budget: session-budget")
    costs = book.line_for("spend-costs-face-slice")
    assert costs.amount == "$0.87"
    assert "Amount: $0.87" in plain_lines(costs)
    flaky = book.line_for("spend-flaky-gate-session")
    assert flaky.period == ""
    assert "Period: unknown" in plain_lines(flaky)
    sweep = book.line_for("spend-store-sweep")
    assert sweep.amount == ""
    assert line_gaps(sweep) == ("spend unknown", "no budget held")
    assert line_counted(sweep) is False
    assert [g.line_id for g in counted_lines(book)] == [
        "spend-login-session", "spend-costs-face-slice",
        "spend-flaky-gate-session", "spend-gallery-slice",
        "spend-bank-wave-slice"]
    assert total_lines(book) == 6
    index = derive_index(book)
    assert [e.budget for e in index.entries] == [
        "session-budget", "slice-budget", "session-budget",
        "slice-budget", "slice-budget"]
    assert index.gaps == ("spend-store-sweep",)
    assert line_for_budget(book, "session-budget").line_id == (
        "spend-login-session")
    assert line_for_budget(book, "triple budget") is None
    assert first_warning(book).warning_id == "warning-gentle-login"
    assert warning_for_subject(
        book, "session-login", "gentle").warning_id == (
            "warning-gentle-login")
    assert warning_for_subject(book, "session-nope") is None


def test_line_record_round_trips():
    line = _line()
    assert validate_line(line) is line
    rebuilt = build_line(_stored_line(line))
    assert rebuilt == line
    assert rebuilt.item_id == "spend-test"
    assert rebuilt.budget == "session-budget"
    record = line_record(line)
    assert record["type"] == "spend_line"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_line_refuses_stored_judgements():
    for key in ("standing", "counted", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_line(_line())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_line(fields)
    fields = _stored_line(_line())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_line(fields)


def test_line_refuses_a_live_session_claim():
    for key in ("resumes_session", "resumed_session", "forks_session",
                "exported_session", "opens_session"):
        fields = _stored_line(_line())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_line(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("exports_session", "resumed_session"):
        fields = _warning().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_warning(fields)
        assert "held as data alone" in str(caught.value)
    record = _warning(subject="spend-test")
    assert validate_warning(record) is record
    assert record.subject == "spend-test"
    assert warning_record(record)["type"] == "costs_warning"


def test_line_vocabularies_are_closed():
    assert _line(scope="SESSION").scope == "session"
    assert _line(amount="").amount == ""
    assert _line(period=None).period == ""
    with pytest.raises(ValueError):
        _line(scope="a hunch")
    with pytest.raises(ValueError):
        _line(label="   ")
    with pytest.raises(ValueError):
        _line(seq=0)
    with pytest.raises(ValueError):
        _line(budget=5)
    with pytest.raises(ValueError):
        _line(amount=5)
    with pytest.raises(ValueError):
        _line(period=5)
    with pytest.raises(ValueError):
        _line(detail="   ")


def test_plain_telling_derives_from_the_lines_own_fields():
    line = _line(
        label="Test Session", scope="slice", amount="", period="",
        budget="", detail="The budget waits on a held line.")
    lines = plain_lines(line)
    assert lines[0] == "Line: Test Session"
    assert lines[1] == "Scope: slice"
    assert lines[2] == "Amount: unknown"
    assert lines[3] == "Period: unknown"
    assert lines[4] == "Budget: none"
    assert plain_words(line) == line_plain_words(line)
    assert "Test Session" in plain_words(line)
    assert "held line" in plain_words(line)


def test_unknown_line_stands_named_in_its_gaps():
    line = _line(budget="")
    assert line_gaps(line) == ("no budget held",)
    assert line_counted(line) is False
    text = format_line(line)
    assert "stands uncounted" in text
    current_text = format_line(_line())
    assert "stands counted" in current_text


def test_view_and_warning_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "costs_view"
    assert record["view_filter"] == "all"
    assert "shows all lines" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    warning = _warning()
    assert build_warning(warning.to_record()) == warning
    assert "Budget warning gentle for spend-test" in format_warning(warning)
    assert "charges nothing" in format_warning(warning)
    assert "at four fifths of the M-107 session budget" in warning_plain_words(warning)
    with pytest.raises(ValueError):
        _warning(level="dance")


# ---------------------------------------------------------------------
# The index and the warning budgets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_lines_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.line_id for e in index.entries] == ["spend-test"]
    assert index.entries[0].budget == "session-budget"
    assert index.gaps == ("spend-unknown",)
    assert index_record(index)["type"] == "costs_index"
    assert index_record(book)["gaps"] == ["spend-unknown"]
    assert "1 budgets" in index_plain_words(book)
    text = format_index(book)
    assert "Spend index" in text
    assert "session-budget - A test session (spend-test)" in text
    assert "spend-unknown" in text
    assert "charges nothing" in text


def test_budget_reaches_its_line_and_an_unheld_budget_reaches_nothing():
    book = _mixed_book()
    assert line_for_budget(book, "session-budget").line_id == "spend-test"
    assert line_for_budget(book, "triple budget") is None
    assert line_for_budget(book, "") is None
    assert "A test session" in format_budget(book, "session-budget")
    assert "reaches nothing in this book" in format_budget(
        book, "triple budget")


def test_first_warning_is_held_as_data():
    book = _book(warnings=[_warning(), _warning(
        warning_id="warning-two", seq=2, subject="session-other",
        level="over", title="The second warning")])
    assert first_warning(book).warning_id == "warning-test"
    assert warning_for_subject(book, "session-other").warning_id == (
        "warning-two")
    assert warning_for_subject(
        book, "session-other", "over").warning_id == "warning-two"
    assert warning_for_subject(book, "session-other", "gentle") is None
    bare = _book()
    assert first_warning(bare) is None
    assert warning_for_subject(bare, "session-other") is None
    text = format_warning(first_warning(book))
    assert "held as data alone" in text
    assert "blocks nothing" in text


def test_warning_budgets_stand_held_whole():
    warning = _warning(
        subject="spend-x", level="near",
        threshold="a branched session")
    assert warning.level == "near"
    rebuilt = build_warning(warning.to_record())
    assert rebuilt == warning
    assert rebuilt.subject == "spend-x"
    assert rebuilt.threshold == "a branched session"
    with pytest.raises(ValueError):
        _warning(subject="   ")
    with pytest.raises(ValueError):
        _warning(threshold="   ")
    with pytest.raises(ValueError):
        _warning(level="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, CostsPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.lines[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.lines[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "costs_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_lines():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, CostsVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "costs_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(lines=[_line()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(lines=[_line(budget="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        lines=[_line(budget="")],
        views=[_view(view_filter="counted")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_scope_readings():
    book = _mixed_book()
    assert [g.line_id for g in shown_lines(book)] == [
        "spend-test", "spend-unknown"]
    counted_view = _view(
        view_id="view-r", seq=2, view_filter="counted")
    book2 = _book(
        lines=[_line(), _line(
            line_id="spend-unknown", seq=2, label="A stopped session",
            scope="slice", amount="", period="", budget="")],
        views=[_view(), counted_view])
    assert [g.line_id for g in shown_lines(book2, counted_view)] == [
        "spend-test"]
    assert [g.line_id for g in lines_for_scope(book2, "slice")] == [
        "spend-unknown"]
    assert [g.line_id for g in counted_lines(book2)] == [
        "spend-test"]
    assert total_lines(book2) == 2
    with pytest.raises(ValueError):
        lines_for_scope(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(lines=[_line(), _line(seq=2)])
    with pytest.raises(ValueError):
        _book(lines=[_line(), _line(line_id="spend-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="counted")])
    with pytest.raises(ValueError) as caught:
        _book(warnings=[_warning(), _warning(warning_id="warning-two", seq=2)])
    assert "one warning stands per session budget" in str(caught.value)
    fields = {
        "schema": COSTS_FACE_SCHEMA, "slice": "M-190",
        "costs": {"title": "A test costs book"},
        "lines": [_stored_line(_line())],
        "views": [_stored_view(_view())], "warnings": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["costs_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": COSTS_FACE_SCHEMA, "slice": "M-190",
        "costs": {"title": "A test costs book"},
        "lines": [], "views": [], "warnings": [], "panels": [],
        "resumes_session": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / COSTS_FACE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "costs_face.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_costs_face_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_lines(book) == 6


def test_registry_holds_lines_and_views_one_by_one():
    registry = CostsFaceRegistry()
    assert registry.list_items() == ()
    held = registry.register_line(_line())
    assert held.line_id == "spend-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["spend-test", "view-test"]
    assert registry.get_line("spend-test").label == "A test session"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld costs book"
    with pytest.raises(ValueError):
        registry.register_line(_line(seq=2))
    with pytest.raises(ValueError):
        registry.register_line(_line(line_id="spend-two"))
    with pytest.raises(KeyError):
        registry.get_line("spend-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = CostsFaceRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test costs book"
    assert len(registry.list_lines()) == 2
    other = _book(lines=[_line(
        line_id="spend-x", seq=9, label="Other", budget="session-budget")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "scope: 'session'" in format_book(book)
    assert "spend-unknown" in format_book(book, "slice")
    assert "spend-test" not in format_book(book, "slice")
    assert "Costs panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The costs book holds 2 lines")
    screen = format_costs_screen(book)
    assert "Costs Face (M-190)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "spend-store-sweep" not in screen
    assert "spend-unknown" in screen
    record = book_record(book)
    assert record["type"] == "costs_book"
    assert record["title"] == "A test costs book"
    assert len(record["lines"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "spend-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    line_text = format_line(book.lines[0])
    assert "Line: A test session" in line_text
    assert "Budget: session-budget" in line_text


def test_parse_args_inspect_and_loader_budgets():
    assert parse_costs_args("") == ("show", None)
    assert parse_costs_args("show") == ("show", None)
    assert parse_costs_args(None) == ("show", None)
    assert parse_costs_args("line spend-test") == (
        "line", "spend-test")
    assert parse_costs_args("budget session-budget") == (
        "budget", "session-budget")
    assert parse_costs_args("scope session") == (
        "scope", "session")
    assert parse_costs_args("view view-test") == ("view", "view-test")
    assert parse_costs_args("warning warning-test") == (
        "warning", "warning-test")
    assert parse_costs_args("index") == ("index", None)
    assert parse_costs_args("panel") == ("panel", None)
    assert parse_costs_args("verdict") == ("verdict", None)
    for bad in ("dance", "line", "budget", "scope", "index now",
                "warning a b"):
        with pytest.raises(ValueError):
            parse_costs_args(bad)
    line = _line()
    assert inspect_costs_source(line) == {
        "kind": "line", "line_id": "spend-test"}
    assert inspect_costs_source(_stored_line(line))["kind"] == (
        "line")
    assert inspect_costs_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_costs_source(_warning().to_record())["kind"] == (
        "warning")
    assert inspect_costs_source(42)["kind"] == "unknown"
    book = load_costs_face({
        "schema": COSTS_FACE_SCHEMA, "slice": "M-190",
        "costs": {"title": "A judged book"},
        "lines": [_stored_line(_line())],
        "views": [_stored_view(_view())], "warnings": [], "panels": []})
    assert isinstance(book, CostsBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_costs_face({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_costs_face({"slice": "M-999"})
    built = build_line(
        line_id="spend-kw", seq=3, label="Kw Session",
        scope="session", amount="$0.01", period="1 minute",
        budget="session-budget", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="spend-test")
    assert built.line_id == "spend-kw"
    assert line_counted(built) is True


# ---------------------------------------------------------------------
# M-190 agent layer: the agent holds a costs book
# for the session, lines and views are published
# as session news through the checkpoint budget
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the index
# is derived from the book's held lines, and the
# warning budgets are held as data beside them -
# holding one resumes no session. This layer
# resumes nothing, renders no live UI, exports
# nothing and persists nothing beyond the
# session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _costs_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_costs_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / COSTS_FACE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "costs_face.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCostsAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.costs_face_status()
        assert status["lines"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["costs"]["title"] == EXAMPLE_TITLE
        assert len(status["costs"]["lines"]) == 6
        assert len(status["costs"]["views"]) == 2
        assert len(status["costs"]["warnings"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m189-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["budget"] for e in status["index"]["entries"]] == [
            "session-budget", "slice-budget", "session-budget",
            "slice-budget", "slice-budget"]
        assert status["index"]["gaps"] == ["spend-store-sweep"]
        assert status["first_warning"]["warning_id"] == "warning-gentle-login"
        assert "held as data alone" in status["rule"]
        assert "Bank the M-189 wave" in status["plain_words"]
        assert "Costs Face (M-190)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._costs_face_registry()
        assert agent._costs_face_registry() is first
        assert agent._costs_face_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.costs_face_status()
        assert agent.get_costs_line(
            "spend-login-session").label == (
                "Fix the login redirect")
        assert agent.get_costs_view("view-all").view_filter == "all"
        assert agent.get_costs_warning(
            "warning-gentle-login").warning_id == "warning-gentle-login"
        assert [a.line_id for a in agent.costs_lines_for_scope(
            "session")] == [
                "spend-login-session", "spend-flaky-gate-session",
                "spend-store-sweep"]
        assert [a.line_id for a in agent.costs_lines_passing()] == [
            "spend-login-session", "spend-costs-face-slice",
            "spend-flaky-gate-session", "spend-gallery-slice",
            "spend-bank-wave-slice"]
        agent.costs_face_panel()
        agent.costs_face_verdict()
        agent.costs_index()
        agent.report_costs_face()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("costs")
                or e["type"] == "spend_line"] == []
        with pytest.raises(KeyError):
            agent.get_costs_line("spend-nope")
        with pytest.raises(KeyError):
            agent.get_costs_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_costs_warning("warning-nope")
        with pytest.raises(ValueError):
            agent.costs_lines_for_scope("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_costs_line(_line())
        status = agent.costs_face_status()
        assert [a["line_id"] for a in status["lines"]] == ["spend-test"]
        assert status["book"]["title"] == "An unheld costs book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["budget"] for e in status["index"]["entries"]] == [
            "session-budget"]
        assert status["first_warning"] is None
        assert "spend-test" in status["screen"]

    def test_held_line_never_falls_back_to_the_example(
            self, agent):
        agent.register_costs_line(_line())
        with pytest.raises(KeyError):
            agent.get_costs_line("spend-login-session")
        with pytest.raises(KeyError):
            agent.get_costs_view("view-all")
        with pytest.raises(KeyError):
            agent.get_costs_warning("modal")
        line = agent.get_costs_line("spend-test")
        assert line.label == "A test session"
        assert agent.costs_face_book().title == (
            "An unheld costs book")

    def test_warnings_and_index_stand_in_the_example(self, agent):
        first = agent.get_costs_warning("warning-gentle-login")
        assert first.warning_id == "warning-gentle-login"
        assert first.subject == "session-login"
        status = agent.costs_face_status()
        assert status["index"]["gaps"] == ["spend-store-sweep"]
        assert status["first_warning"]["subject"] == (
            "session-login")
        assert status["first_warning"]["level"] == "gentle"


class TestCostsAgentHolding:
    def test_register_line_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_costs_line(_line())
        assert result["line"]["line_id"] == "spend-test"
        assert result["record_news"]["type"] == "spend_line"
        assert "spend-test" in result["screen"]
        events = _costs_events(store, session_id, "spend_line")
        assert len(events) == 1
        agent.close()

    def test_duplicate_line_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_costs_line(_line())
        with pytest.raises(ValueError):
            agent.register_costs_line(_line(seq=9))
        with pytest.raises(ValueError):
            agent.register_costs_line(_line(line_id="spend-two"))
        events = _costs_events(store, session_id, "spend_line")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_costs_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_costs_events(
            store, session_id, "costs_view")) == 1
        agent.close()

    def test_view_budget_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_costs_line(_line())
        result = agent.view_costs("counted")
        assert result["view"]["view_filter"] == "counted"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "costs_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_costs_events(
            store, session_id, "costs_view")) == 1
        assert len(_costs_events(
            store, session_id, "costs_panel")) == 1
        assert len(_costs_events(
            store, session_id, "costs_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_costs_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "spend_line", "costs_view"]
        assert len(_costs_events(
            store, session_id, "spend_line")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_costs_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "costs_panel"
        assert result["index_record"]["gaps"] == [
            "spend-store-sweep"]
        with pytest.raises(ValueError):
            agent.record_costs_book()
        assert len(_costs_events(
            store, session_id, "spend_line")) == 6
        assert len(_costs_events(
            store, session_id, "costs_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_costs_book_file(tmp_path)
        book = load_costs_face_file(path)
        result = agent.record_costs_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_costs_face()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["spend-store-sweep"]
        assert "spend-login-session" in report["book_text"]
        assert "session-budget - Fix the login redirect" in report["index_text"]
        agent.register_costs_line(_line())
        report = agent.report_costs_face()
        assert report["book"]["title"] == "An unheld costs book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestCostsTerminalSurface:
    def test_show_line_budget_scope_view_warning_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/costs")
        assert "Costs Face (M-190)" in text
        _, _, text = _slash(agent, "/costs line spend-login-session")
        assert "Line: Fix the login redirect" in text
        _, _, text = _slash(agent, "/costs budget session-budget")
        assert "Fix the login redirect" in text
        _, _, text = _slash(agent, "/costs budget triple-budget")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/costs scope slice")
        assert "spend-costs-face-slice" in text
        assert "spend-login-session" not in text
        _, _, text = _slash(agent, "/costs view view-all")
        assert "filter all" in text
        _, _, text = _slash(agent, "/costs warning warning-gentle-login")
        assert "Budget warning gentle for session-login" in text
        _, _, text = _slash(agent, "/costs index")
        assert "Spend index" in text
        assert "spend-gallery-slice" in text
        _, _, text = _slash(agent, "/costs panel")
        assert "Costs panel under view view-all" in text
        _, _, text = _slash(agent, "/costs verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/costs [show|line <line-id>"
                "|budget <budget>|scope <scope>|view <view-id>"
                "|warning <warning-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/costs dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/costs line spend-nope")
        assert "no line named" in text


@pytest.fixture()
def costs_handler(agent, monkeypatch):
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


def _costs_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCostsCommand:
    def test_show_is_default(self, costs_handler, agent):
        costs_handler._handle_costs("")
        assert "Costs Face (M-190)" in (
            _costs_published_text(costs_handler))

    def test_line_budget_scope_view_warning_index_panel_verdict(
            self, costs_handler, agent):
        costs_handler._handle_costs("line spend-login-session")
        assert "Line: Fix the login redirect" in _costs_published_text(
            costs_handler)
        costs_handler._handle_costs("budget session-budget")
        assert "Fix the login redirect" in _costs_published_text(
            costs_handler)
        costs_handler._handle_costs("scope completed")
        assert "spend-login-session" in _costs_published_text(costs_handler)
        costs_handler._handle_costs("view view-all")
        assert "filter all" in _costs_published_text(costs_handler)
        costs_handler._handle_costs("warning warning-gentle-login")
        assert "Budget warning gentle for session-login" in _costs_published_text(costs_handler)
        costs_handler._handle_costs("index")
        assert "Spend index" in _costs_published_text(costs_handler)
        costs_handler._handle_costs("panel")
        assert "Costs panel under view" in _costs_published_text(
            costs_handler)
        costs_handler._handle_costs("verdict")
        assert "strained" in _costs_published_text(costs_handler)

    def test_bad_grammar_is_published(
            self, costs_handler, agent):
        costs_handler._handle_costs("dance party")
        assert USAGE in _costs_published_text(costs_handler)
        costs_handler._handle_costs("line spend-nope")
        assert "no line named" in _costs_published_text(costs_handler)


class TestChatScreenRoutingCosts:
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
        screen.handle_command("/costs panel", _FakeLog())
        assert calls == [("/costs", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/costs[/green] - show costs face (M-190)" in (
            text)
        assert ('"/costs": "Usage: /costs | '
                '/costs line <line-id>') in text


class TestCostsDerivedRoads:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.costs_face_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-all"
        verdict = agent.costs_face_verdict()
        assert verdict.verdict == "strained"
        found = agent.costs_face_verdict("view-counted")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_costs_line(_line())
        with pytest.raises(ValueError):
            agent.costs_face_panel()
        with pytest.raises(ValueError):
            agent.costs_face_verdict()

    def test_view_budget_over_an_unshown_filter_is_shut(self, agent):
        agent.register_costs_line(_line(budget=""))
        result = agent.view_costs("counted")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_budget_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.costs_index()
        assert [e["budget"] for e in result["index"]["entries"]] == [
            "session-budget", "slice-budget", "session-budget",
            "slice-budget", "slice-budget"]
        assert result["index"]["gaps"] == ["spend-store-sweep"]
        assert "session-budget - Fix the login redirect (spend-login-session)" in (
            result["index_text"])
        line = agent.get_costs_line("spend-store-sweep")
        assert line_gaps(line) == ("spend unknown", "no budget held")
        assert line_counted(line) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("costs")
                or e["type"] == "spend_line"] == []
        agent.close()
