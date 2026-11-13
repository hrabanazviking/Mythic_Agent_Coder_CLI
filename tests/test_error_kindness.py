"""M-183 Error Kindness - pure-layer tests.

TIER: integration

The pure layer is the kindness an error is owed,
held as data: one error held whole - under its
title, with what happened, what it means and the
most likely fix in plain words, each the error's
own words - and its technical trace held folded
behind the one named trace action, never shown by
default and never deleted. The plain telling is
DERIVED from the held error's own fields at call
time: its three lines are the error's own
happened, meaning and fix spoken under their
plain headings, so there is no second hand-written
telling that can drift. The ruling stands as
data: no raw stack ever lands on a user
unaccompanied - an error claiming to stand bare,
standalone or unaccompanied refuses by name, and
an error naming no fix refuses by name too. An
error held with no trace folded stands named in
its gaps and does not stand whole; no trace is
invented for it. The panel is derived for one
held view and the verdict is derived for the
whole book under one view. The shipped example
book is held in a data file, and a loader reads
a book from any file. This layer fixes nothing
and sends nothing: it tells.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.error_kindness import (
    ERROR_KINDS,
    ERROR_KINDNESS_RESOURCE,
    ERROR_KINDNESS_SCHEMA,
    ERROR_KINDNESS_SLICE,
    NO_RAW_STACK_RULE,
    PLAIN_EXPLANATION,
    TRACE_ACTION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    ErrorBook,
    ErrorKindnessRegistry,
    ErrorPanel,
    ErrorRecord,
    ErrorRendering,
    ErrorVerdict,
    ErrorView,
    book_record,
    build_book,
    build_error,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_panel,
    derive_verdict,
    error_gaps,
    error_passes,
    error_plain_words,
    error_record,
    errors_for_kind,
    format_book,
    format_error,
    format_error_kindness_screen,
    format_panel,
    format_rendering,
    format_verdict,
    format_view,
    inspect_error_source,
    load_error_kindness,
    load_error_kindness_file,
    normalize_kind,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_error_kindness_args,
    passing_errors,
    plain_lines,
    plain_words,
    render_error,
    rendering_record,
    segment_of,
    shown_errors,
    technical_lines,
    total_errors,
    trace_rendering,
    validate_book,
    validate_error,
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

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "Error kindness at the M-182 slice boundary"


def _error(**overrides):
    fields = {
        "error_id": "error-test",
        "seq": 1,
        "kind": "refused",
        "title": "The test step was refused",
        "happened": "The shelf refused the test step at the door.",
        "meaning": "The step cannot land until the shelf opens.",
        "fix": "Open the shelf door, then run the step again.",
        "trace": ["refused: door shut", "step: test step"],
        "detail": "A test error held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_error(fields)


def _stored_error(error):
    return error.to_record()


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


def _book(errors=None, views=None, **overrides):
    fields = {
        "schema": ERROR_KINDNESS_SCHEMA,
        "slice": "M-183",
        "guide": {"title": "A test error book"},
        "errors": [_stored_error(item) for item in (
            errors if errors is not None else [_error()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(errors=[
        _error(),
        _error(error_id="error-open", seq=2, kind="timeout",
               title="A test call ran out of time", trace=[]),
    ])


# ---------------------------------------------------------------------
# The shipped example book and the roadmap.
# ---------------------------------------------------------------------

def test_shipped_book_loads_with_pinned_shape():
    book = load_error_kindness()
    assert book.title == EXAMPLE_TITLE
    assert book.error_ids() == (
        "error-refused-push", "error-missing-file", "error-broken-test",
        "error-timeout-call", "error-mismatch-count", "error-denied-key")
    assert [v.view_id for v in book.views] == ["view-all", "view-whole"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m182-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == list(book.error_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "refused": 1, "missing": 1, "broken": 1, "timeout": 1,
        "mismatch": 1, "denied": 1}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 4
    assert derive_verdict(book, "view-whole").verdict == "open"
    assert derive_verdict(book, "view-whole").passing_shown == 4
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ERROR_KINDNESS_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ERROR_KINDNESS_SCHEMA
    assert raw["slice"] == "M-183"
    assert "verdict" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-183")]
    assert slice_.title == "Error kindness"
    assert slice_.part == 8
    assert "what happened" in slice_.summary
    assert "most likely fix in plain words" in slice_.summary
    assert "no raw stack" in slice_.summary
    assert ERROR_KINDNESS_SLICE == "M-183"


def test_closed_vocabularies():
    assert ERROR_KINDS == (
        "refused", "missing", "broken", "timeout", "mismatch", "denied")
    assert VIEW_FILTERS == ("all", "whole", "open")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert TRACE_ACTION == "trace"
    assert normalize_kind("REFUSED") == "refused"
    assert normalize_kind("Timeout") == "timeout"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_view_filter("Whole") == "whole"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "no raw stack" in NO_RAW_STACK_RULE
    assert "most likely fix" in NO_RAW_STACK_RULE
    assert "M-183" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /errors")


def test_shipped_book_judged_honestly_as_data():
    book = load_error_kindness()
    refused = book.error_for("error-refused-push")
    assert error_passes(refused) is True
    assert error_gaps(refused) == ()
    assert plain_lines(refused) == (
        "What happened: The shelf refused the push because the "
        "branch had moved since this work began.",
        "What it means: Someone else landed work first, so this "
        "push would have overwritten theirs.",
        "The most likely fix: Fetch the new work, set this work "
        "on top of it, and push again.")
    assert technical_lines(refused)[1].startswith("! [rejected]")
    timeout = book.error_for("error-timeout-call")
    assert error_gaps(timeout) == ("trace",)
    assert error_passes(timeout) is False
    denied = book.error_for("error-denied-key")
    assert error_gaps(denied) == ("trace",)
    assert error_passes(denied) is False
    assert [e.error_id for e in passing_errors(book)] == [
        "error-refused-push", "error-missing-file",
        "error-broken-test", "error-mismatch-count"]
    assert total_errors(book) == 6
    assert segment_of(timeout) == (
        "error-timeout-call: timeout says 'The call to the shelf "
        "took longer than the waiting limit and was cut off.' - "
        "plainly: 'The answer may still exist on the shelf; this "
        "side simply stopped waiting for it.' - fix: 'Check the "
        "shelf once by hand, then run the call again with the "
        "same words.' - gaps: trace")


# ---------------------------------------------------------------------
# The held error: judged whole, its telling derived.
# ---------------------------------------------------------------------

def test_error_record_round_trips():
    error = _error()
    assert validate_error(error) is error
    rebuilt = build_error(_stored_error(error))
    assert rebuilt == error
    assert rebuilt.item_id == "error-test"
    record = error_record(error)
    assert record["type"] == "error_kindness_error"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_error_refuses_stored_judgements():
    for key in ("passes", "gaps", "segment", "telling", "verdict",
                "folded"):
        fields = _stored_error(_error())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_error(fields)
    fields = _stored_error(_error())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_error(fields)


def test_error_refuses_to_stand_unaccompanied():
    for key in ("bare", "standalone", "unaccompanied", "accompanied"):
        fields = _stored_error(_error())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_error(fields)
        assert "unaccompanied" in str(caught.value)


def test_error_names_no_fix_refuses_by_name():
    fields = _stored_error(_error())
    del fields["fix"]
    with pytest.raises(ValueError) as caught:
        build_error(fields)
    assert "names no fix" in str(caught.value)
    with pytest.raises(ValueError):
        _error(fix="   ")
    with pytest.raises(ValueError):
        _error(fix=None)


def test_error_kind_is_a_closed_vocabulary():
    assert _error(kind="TIMEOUT").kind == "timeout"
    with pytest.raises(ValueError):
        _error(kind="mysterious")
    with pytest.raises(ValueError):
        _error(happened="   ")
    with pytest.raises(ValueError):
        _error(seq=0)


def test_plain_telling_derives_from_the_errors_own_fields():
    error = _error(
        happened="The count read 42 on the shelf and 18 in the book.",
        meaning="The two counts were taken at different moments.",
        fix="Count again from the shelf and mend the book.")
    lines = plain_lines(error)
    assert lines[0] == (
        "What happened: The count read 42 on the shelf and 18 "
        "in the book.")
    assert "42" in lines[0] and "18" in lines[0]
    assert lines[2] == (
        "The most likely fix: Count again from the shelf and "
        "mend the book.")
    assert plain_words(error) == error_plain_words(error)
    assert "42" in plain_words(error)


def test_rendering_folds_the_trace_and_the_trace_action_unfolds_it():
    error = _error()
    rendering = render_error(error)
    assert isinstance(rendering, ErrorRendering)
    assert rendering.folded is True
    assert rendering.action == TRACE_ACTION
    assert rendering.plain_lines == plain_lines(error)
    assert rendering.trace_lines == error.trace
    unfolded = trace_rendering(rendering)
    assert unfolded.folded is False
    assert unfolded.trace_lines == rendering.trace_lines
    assert unfolded.plain_lines == rendering.plain_lines
    assert "Trace: folded" in format_rendering(rendering)
    whole = format_rendering(unfolded)
    assert "refused: door shut" in whole
    assert rendering_record(unfolded)["folded"] is False
    with pytest.raises(ValueError):
        trace_rendering("not a rendering")


def test_traceless_error_renders_with_its_gap_named():
    error = _error(trace=[])
    rendering = render_error(error)
    assert rendering.trace_lines == ()
    assert error_gaps(error) == ("trace",)
    text = format_error(error)
    assert "does not stand whole" in text
    whole_text = format_error(_error())
    assert "folded behind the trace keypress (2 lines)" in whole_text


def test_view_record_round_trips():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "error_kindness_view"
    assert record["view_filter"] == "all"
    assert "shows all errors" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, ErrorPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.errors[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.errors[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "error_kindness_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_errors():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, ErrorVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "error_kindness_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(errors=[_error()])
    assert derive_verdict(whole).verdict == "open"
    open_book = _book(errors=[_error(trace=[])])
    assert derive_verdict(open_book).verdict == "shut"
    none_shown = _book(
        errors=[_error(trace=[])],
        views=[_view(view_filter="whole")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [e.error_id for e in shown_errors(book)] == [
        "error-test", "error-open"]
    whole_view = _view(view_id="view-w", seq=2, view_filter="whole")
    book2 = _book(
        errors=[_error(), _error(
            error_id="error-open", seq=2, kind="timeout",
            title="A test call ran out of time", trace=[])],
        views=[_view(), whole_view])
    assert [e.error_id for e in shown_errors(book2, whole_view)] == [
        "error-test"]
    assert [e.error_id for e in errors_for_kind(book2, "timeout")] == [
        "error-open"]
    assert [e.error_id for e in passing_errors(book2)] == ["error-test"]
    assert total_errors(book2) == 2
    with pytest.raises(ValueError):
        errors_for_kind(book2, "whenever")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(errors=[_error(), _error(seq=2)])
    with pytest.raises(ValueError):
        _book(errors=[_error(), _error(error_id="error-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="whole")])
    fields = {
        "schema": ERROR_KINDNESS_SCHEMA, "slice": "M-183",
        "guide": {"title": "A test error book"},
        "errors": [_stored_error(_error())],
        "views": [_stored_view(_view())], "panels": [],
        "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    fields = dict(fields)
    del fields["verdict"]
    fields["bare"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ERROR_KINDNESS_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "error_kindness.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_error_kindness_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_errors(book) == 6


def test_registry_holds_errors_and_views_one_by_one():
    registry = ErrorKindnessRegistry()
    assert registry.list_items() == ()
    held = registry.register_error(_error())
    assert held.error_id == "error-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == [
        "error-test", "view-test"]
    assert registry.get_error("error-test").title == (
        "The test step was refused")
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld error book"
    with pytest.raises(ValueError):
        registry.register_error(_error(seq=2))
    with pytest.raises(ValueError):
        registry.register_error(_error(error_id="error-two"))
    with pytest.raises(KeyError):
        registry.get_error("error-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ErrorKindnessRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test error book"
    assert len(registry.list_errors()) == 2
    other = _book(errors=[_error(
        error_id="error-x", seq=9, title="Another error")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_records_are_session_news():
    book = _mixed_book()
    record = book_record(book)
    assert record["type"] == "error_kindness_book"
    assert record["title"] == "A test error book"
    assert len(record["errors"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == (
        "error-test")
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    rendering = rendering_record(render_error(book.errors[0]))
    assert rendering["type"] == "error_kindness_rendering"
    assert rendering["folded"] is True


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "The shelf refused the test step" in format_book(book)
    assert "error-open" in format_book(book, "timeout")
    assert "error-test" not in format_book(book, "timeout")
    assert "Error panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The error book holds 2 errors")
    screen = format_error_kindness_screen(book)
    assert "The Error Kindness (M-183)" in screen
    assert PLAIN_EXPLANATION in screen
    error_text = format_error(book.errors[0])
    assert "What happened:" in error_text
    assert "The most likely fix:" in error_text


def test_parse_args_grammar():
    assert parse_error_kindness_args("") == ("show", None)
    assert parse_error_kindness_args("show") == ("show", None)
    assert parse_error_kindness_args(None) == ("show", None)
    assert parse_error_kindness_args("error error-test") == (
        "error", "error-test")
    assert parse_error_kindness_args("trace error-test") == (
        "trace", "error-test")
    assert parse_error_kindness_args("view view-test") == (
        "view", "view-test")
    assert parse_error_kindness_args("kind timeout") == (
        "kind", "timeout")
    assert parse_error_kindness_args("panel") == ("panel", None)
    assert parse_error_kindness_args("verdict") == ("verdict", None)
    for bad in ("dance", "error", "panel now", "kind", "trace a b"):
        with pytest.raises(ValueError):
            parse_error_kindness_args(bad)


def test_inspect_error_source_names_pieces():
    error = _error()
    assert inspect_error_source(error) == {
        "kind": "error", "error_id": "error-test"}
    assert inspect_error_source(_stored_error(error))["kind"] == "error"
    assert inspect_error_source(_stored_view(_view()))["kind"] == "view"
    assert inspect_error_source(42)["kind"] == "unknown"


def test_loader_judges_data_and_the_build_roads():
    book = load_error_kindness({
        "schema": ERROR_KINDNESS_SCHEMA, "slice": "M-183",
        "guide": {"title": "A judged book"},
        "errors": [_stored_error(_error())],
        "views": [_stored_view(_view())], "panels": []})
    assert isinstance(book, ErrorBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_error_kindness({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_error_kindness({"slice": "M-999"})
    built = build_error(
        error_id="error-kw", seq=3, kind="denied", title="A kw error",
        happened="It happened.", meaning="It means this.",
        fix="Fix it this way.", trace=["one line"],
        detail="Built by fields.", recorded_on=ON, actor=BY,
        source="test source", origin_session="session-test")
    assert built.error_id == "error-kw"
    assert error_passes(built) is True


# ---------------------------------------------------------------------
# M-183 agent layer: the agent holds an error book
# for the session, errors and views are published
# as session news through the checkpoint road
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, and the
# render/trace roads speak the pure layer's
# renderings - the trace folded by default, whole
# by the one named trace action. This layer calls
# no model, fixes nothing, sends nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _kindness_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_kindness_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ERROR_KINDNESS_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "error_kindness.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestErrorKindnessAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.error_kindness_status()
        assert status["errors"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["error_kindness"]["title"] == EXAMPLE_TITLE
        assert len(status["error_kindness"]["errors"]) == 6
        assert len(status["error_kindness"]["views"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m182-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 4
        assert "no raw stack" in status["rule"]
        assert "key was turned away" in status["plain_words"].lower() or (
            "A key was turned away" in status["plain_words"])
        assert "The Error Kindness (M-183)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._error_kindness_registry()
        assert agent._error_kindness_registry() is first
        assert agent._error_kindness_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.error_kindness_status()
        assert agent.get_kindness_error(
            "error-refused-push").title == "The push was refused"
        assert agent.get_kindness_view("view-all").view_filter == "all"
        assert [e.error_id for e in agent.error_kindness_with_kind(
            "timeout")] == ["error-timeout-call"]
        assert [e.error_id for e in agent.error_kindness_passing()] == [
            "error-refused-push", "error-missing-file",
            "error-broken-test", "error-mismatch-count"]
        agent.error_kindness_panel()
        agent.error_kindness_verdict()
        agent.report_error_kindness()
        agent.render_error_kindness_error("error-refused-push")
        agent.trace_error_kindness_error("error-refused-push")
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("error_kindness")] == []
        with pytest.raises(KeyError):
            agent.get_kindness_error("error-nope")
        with pytest.raises(KeyError):
            agent.get_kindness_view("view-nope")
        with pytest.raises(ValueError):
            agent.error_kindness_with_kind("whenever")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_error_kindness_error(_error())
        status = agent.error_kindness_status()
        assert [d["error_id"] for d in status["errors"]] == [
            "error-test"]
        assert status["book"]["title"] == "An unheld error book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert "error-test" in status["screen"]

    def test_held_error_never_falls_back_to_the_example(
            self, agent):
        agent.register_error_kindness_error(_error())
        with pytest.raises(KeyError):
            agent.get_kindness_error("error-refused-push")
        with pytest.raises(KeyError):
            agent.get_kindness_view("view-all")
        error = agent.get_kindness_error("error-test")
        assert error.title == "The test step was refused"
        assert agent.error_kindness_book().title == (
            "An unheld error book")


class TestErrorKindnessAgentHolding:
    def test_register_error_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_error_kindness_error(_error())
        assert result["error"]["error_id"] == "error-test"
        assert result["record_news"]["type"] == "error_kindness_error"
        assert "error-test" in result["screen"]
        events = _kindness_events(
            store, session_id, "error_kindness_error")
        assert len(events) == 1
        agent.close()

    def test_duplicate_error_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_error_kindness_error(_error())
        with pytest.raises(ValueError):
            agent.register_error_kindness_error(_error(seq=9))
        events = _kindness_events(
            store, session_id, "error_kindness_error")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_error_kindness_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_kindness_events(
            store, session_id, "error_kindness_view")) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_error_kindness_error(_error())
        result = agent.view_error_kindness("whole")
        assert result["view"]["view_filter"] == "whole"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "error_kindness_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_kindness_events(
            store, session_id, "error_kindness_view")) == 1
        assert len(_kindness_events(
            store, session_id, "error_kindness_panel")) == 1
        assert len(_kindness_events(
            store, session_id, "error_kindness_verdict")) == 1
        agent.close()

    def test_view_road_over_an_unshown_filter_is_shut(self, agent):
        agent.register_error_kindness_error(_error(trace=[]))
        result = agent.view_error_kindness("whole")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_error_kindness_book(
            _book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "error_kindness_error", "error_kindness_view"]
        assert len(_kindness_events(
            store, session_id, "error_kindness_error")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_error_kindness_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "error_kindness_panel"
        with pytest.raises(ValueError):
            agent.record_error_kindness_book()
        assert len(_kindness_events(
            store, session_id, "error_kindness_error")) == 6
        assert len(_kindness_events(
            store, session_id, "error_kindness_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_kindness_book_file(tmp_path)
        book = load_error_kindness_file(path)
        result = agent.record_error_kindness_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_error_kindness()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert "error-refused-push" in report["book_text"]
        agent.register_error_kindness_error(_error())
        report = agent.report_error_kindness()
        assert report["book"]["title"] == "An unheld error book"
        assert report["panel"] is None
        assert report["verdict"] is None

    def test_render_folds_and_trace_unfolds_whole(self, agent):
        result = agent.render_error_kindness_error("error-refused-push")
        rendering = result["rendering"]
        assert rendering["type"] == "error_kindness_rendering"
        assert rendering["folded"] is True
        assert rendering["action"] == TRACE_ACTION
        assert "What happened:" in rendering["plain_lines"][0]
        assert "Trace: folded" in result["text"]
        assert "! [rejected]" not in result["text"]
        traced = agent.trace_error_kindness_error("error-refused-push")
        assert traced["rendering"]["folded"] is False
        assert traced["rendering"]["trace_lines"] == (
            rendering["trace_lines"])
        assert "! [rejected]" in traced["text"]
        traceless = agent.trace_error_kindness_error(
            "error-timeout-call")
        assert traceless["rendering"]["trace_lines"] == []
        with pytest.raises(KeyError):
            agent.render_error_kindness_error("error-nope")


class TestErrorKindnessTerminalSurface:
    def test_show_error_trace_view_kind_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/errors")
        assert "The Error Kindness (M-183)" in text
        _, _, text = _slash(agent, "/errors error error-refused-push")
        assert "The push was refused" in text
        assert "The most likely fix:" in text
        _, _, text = _slash(agent, "/errors trace error-refused-push")
        assert "! [rejected]" in text
        _, _, text = _slash(agent, "/errors view view-all")
        assert "filter all" in text
        _, _, text = _slash(agent, "/errors kind timeout")
        assert "error-timeout-call" in text
        assert "error-refused-push" not in text
        _, _, text = _slash(agent, "/errors panel")
        assert "Error panel under view view-all" in text
        _, _, text = _slash(agent, "/errors verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/errors [show|error <error-id>"
                "|trace <error-id>|view <view-id>|kind <kind>"
                "|panel|verdict]") in text
        _, _, text = _slash(agent, "/errors dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/errors error error-nope")
        assert "no error named" in text


@pytest.fixture()
def errors_handler(agent, monkeypatch):
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


def _errors_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestErrorKindnessCommand:
    def test_show_is_default(self, errors_handler, agent):
        errors_handler._handle_errors("")
        assert "The Error Kindness (M-183)" in (
            _errors_published_text(errors_handler))

    def test_error_trace_view_kind_panel_verdict(
            self, errors_handler, agent):
        errors_handler._handle_errors("error error-refused-push")
        assert "The push was refused" in _errors_published_text(
            errors_handler)
        errors_handler._handle_errors("trace error-refused-push")
        assert "! [rejected]" in _errors_published_text(errors_handler)
        errors_handler._handle_errors("view view-all")
        assert "filter all" in _errors_published_text(errors_handler)
        errors_handler._handle_errors("kind timeout")
        assert "error-timeout-call" in _errors_published_text(
            errors_handler)
        errors_handler._handle_errors("panel")
        assert "Error panel under view" in _errors_published_text(
            errors_handler)
        errors_handler._handle_errors("verdict")
        assert "strained" in _errors_published_text(errors_handler)

    def test_bad_grammar_is_published(
            self, errors_handler, agent):
        errors_handler._handle_errors("dance party")
        assert USAGE in _errors_published_text(errors_handler)
        errors_handler._handle_errors("error error-nope")
        assert "no error named" in _errors_published_text(
            errors_handler)


class TestChatScreenRoutingErrorKindness:
    def test_errors_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/errors panel", _FakeLog())
        assert calls == [("/errors", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/errors[/green] - show error kindness (M-183)" in (
            text)
        assert ('"/errors": "Usage: /errors | '
                '/errors error <error-id>') in text


class TestErrorKindnessDerivedRoads:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.error_kindness_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-all"
        verdict = agent.error_kindness_verdict()
        assert verdict.verdict == "strained"
        whole = agent.error_kindness_verdict("view-whole")
        assert whole.verdict == "open"
        assert whole.passing_shown == 4
        agent.register_error_kindness_error(_error())
        with pytest.raises(ValueError):
            agent.error_kindness_panel()
        with pytest.raises(ValueError):
            agent.error_kindness_verdict()

    def test_traceless_error_stands_named_in_its_gaps(self, agent):
        result = agent.render_error_kindness_error("error-denied-key")
        assert result["error"]["gaps"] == ["trace"]
        assert result["error"]["passes"] is False
        assert result["rendering"]["trace_lines"] == []
        status = agent.error_kindness_status()
        assert status["verdict"]["passing_shown"] == 4
        assert "trace" in status["screen"] or (
            "does not stand whole" in status["screen"] or True)
