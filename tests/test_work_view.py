"""M-172 Streaming Work View - pure-layer tests.

TIER: integration

The pure layer is the work event, held as data:
one coder action - its kind in the closed kind
set, the target it touches, the tool that
carries it, the tool detail it holds back, its
state as a word, and its provenance whole (the
day it happened, who acted, its source and the
session it happened in). The narrative line is
derived, never chosen: a started action speaks
in the present with an ellipsis, a done action
in the past, a failed action as a could-not -
and the tool detail never crosses into the
narrative, the panel or the verdict; it stands
only on the detail road, one keystroke away. A
work panel is derived from the whole book (its
rows the events in stream order, its current
event the last action still standing started),
a work verdict is derived for the whole book,
an event is composed by import from a shipped
tool call - its kind judged from the shipped
tool's own name - the shipped example book is
held in a data file, and a loader reads a book
from any file. Nothing here runs a tool, streams
anything live, sends, posts, schedules, calls a
model or persists anything: an event held here
is a record of work, never the work itself.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tool_schemas import get_agent_tools
from mythic_agent.core.tui_redesign_charter import load_charter
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.work_view import (
    KINDS,
    PLAIN_EXPLANATION,
    STATES,
    TOOL_KINDS,
    USAGE,
    VERDICT_WORDS,
    WORK_VIEW_RESOURCE,
    WORK_VIEW_SCHEMA,
    WORK_VIEW_SLICE,
    KindCount,
    WorkBook,
    WorkEvent,
    WorkPanel,
    WorkRegistry,
    WorkVerdict,
    book_record,
    build_book,
    build_event,
    build_panel,
    build_row,
    build_verdict,
    derive_panel,
    derive_verdict,
    detail_of,
    detail_plain_words,
    event_from_tool_call,
    event_record,
    events_of_kind,
    format_event,
    format_event_detail,
    format_panel,
    format_stream,
    format_verdict,
    format_work_view_screen,
    inspect_action_source,
    kind_for_tool,
    load_work_view,
    load_work_view_file,
    narrative_of,
    normalize_kind,
    normalize_state,
    panel_plain_words,
    panel_record,
    parse_work_view_args,
    plain_words,
    total_events,
    validate_event,
    validate_panel,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Streaming Work View at the M-171 slice boundary"

BY = "the coder"
ON = "2026-11-09"
DETAIL = "read_file auth.py - 120 lines, the login road whole."


def _event(**overrides):
    fields = {
        "event_id": "event-test",
        "seq": 1,
        "kind": "reading",
        "target": "auth.py",
        "tool": "read_file",
        "detail": DETAIL,
        "state": "done",
        "occurred_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_event(fields)


def _stored_event(event):
    stored = event.to_record()
    for key in ("type", "slice", "narrative"):
        stored.pop(key)
    return stored


def _book(events=None, **overrides):
    fields = {
        "title": "A test work book",
        "events": [_stored_event(item) for item in (
            events if events is not None else [_event()])],
    }
    fields.update(overrides)
    return build_book(fields)


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_work_view()
    assert book.title == EXAMPLE_TITLE
    assert book.event_ids() == (
        "event-screens-read", "event-kindness-searched",
        "event-charter-data-written",
        "event-charter-module-edited",
        "event-charter-tests-run", "event-verdicts-checked")
    first = book.events[0]
    assert first.target == "mythic_agent/ui/screens/chat_screen.py"
    assert narrative_of(first) == (
        "read `mythic_agent/ui/screens/chat_screen.py`")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m171-boundary"
    assert panel.as_of == "2026-11-09"
    assert panel == derive_panel(book) or (
        panel.rows == derive_panel(book).rows
        and panel.account == derive_panel(book).account)
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / WORK_VIEW_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == WORK_VIEW_SCHEMA
    assert raw["slice"] == "M-172"


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-172")]
    assert slice_.title == "Streaming work view"
    assert slice_.part == 8
    assert "calm narrative" in slice_.summary
    assert "one keystroke away" in slice_.summary
    assert WORK_VIEW_SLICE == "M-172"


def test_charter_names_m172_for_both_repaired_screens():
    charter = load_charter()
    assert "M-172" in charter.screen("main_chat").owning_slices
    assert "M-172" in charter.screen("terminal_loop").owning_slices
    assert charter.screen("main_chat").verdict == "repair"
    assert charter.screen("terminal_loop").verdict == "repair"


def test_closed_vocabularies():
    assert KINDS == (
        "reading", "editing", "writing", "searching",
        "running-tests", "running-command", "checking",
        "thinking")
    assert STATES == ("started", "done", "failed")
    assert VERDICT_WORDS == ("calm", "working", "troubled")
    assert normalize_kind("tests") == "running-tests"
    assert normalize_kind("edit") == "editing"
    assert normalize_state("running") == "started"
    assert normalize_state("passed") == "done"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_state("whenever")
    assert "one keystroke away" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /workview")


def test_tool_kinds_are_the_shipped_tools():
    shipped = {
        tool["function"]["name"] for tool in get_agent_tools()}
    assert set(TOOL_KINDS) <= shipped
    assert TOOL_KINDS["read_file"] == "reading"
    assert TOOL_KINDS["replace_file_content"] == "editing"
    assert TOOL_KINDS["grep_search"] == "searching"


# ---------------------------------------------------------------------
# The event: judged whole, its narrative derived.
# ---------------------------------------------------------------------


def test_event_record_round_trips():
    event = _event()
    assert build_event(_stored_event(event)) == event
    assert event.to_record()["narrative"] == "read `auth.py`"
    assert event.to_record()["type"] == "work_view_event"


def test_event_provenance_is_whole_and_required():
    event = _event()
    assert event.actor == BY
    assert event.origin_session == "session-test"
    for missing in ("seq", "kind", "target", "tool", "detail",
                    "state", "occurred_on", "actor", "source",
                    "origin_session"):
        fields = _stored_event(event)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_event(fields)


def test_event_refuses_unknown_keys_and_split_spellings():
    fields = _stored_event(_event())
    fields["narrative"] = "read `auth.py`"
    with pytest.raises(ValueError):
        build_event(fields)
    fields = _stored_event(_event())
    fields["sequence"] = 99
    with pytest.raises(ValueError):
        build_event(fields)
    fields = _stored_event(_event())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_event(fields)


def test_event_alias_spellings_read_onto_the_fields():
    event = build_event({
        "id": "event-alias", "sequence": 3, "action": "edit",
        "target": "auth.py", "tool": "replace_file_content",
        "detail": "one hunk replaced.", "status": "finished",
        "day": ON, "by": BY, "source": "alias source",
        "session": "session-alias"})
    assert event.kind == "editing"
    assert event.state == "done"
    assert event.seq == 3


def test_narrative_is_derived_per_kind_and_state():
    assert narrative_of(_event(state="started")) == (
        "reading `auth.py`\u2026")
    assert narrative_of(_event(state="done")) == "read `auth.py`"
    assert narrative_of(_event(state="failed")) == (
        "could not read `auth.py`")
    assert narrative_of(_event(
        kind="editing", tool="replace_file_content",
        state="started")) == "editing `auth.py`\u2026"
    assert narrative_of(_event(
        kind="running-tests", tool="run_command",
        target="the test suite", state="started")) == (
        "running tests\u2026")
    assert narrative_of(_event(
        kind="running-tests", tool="run_command",
        target="the test suite", state="done")) == "ran the tests"
    assert narrative_of(_event(
        kind="searching", tool="grep_search", target="K-05",
        state="done")) == "searched for K-05"
    assert narrative_of(_event(
        kind="running-command", tool="run_command",
        target="git status", state="started")) == (
        "running `git status`\u2026")


def test_narrative_never_carries_the_detail_or_the_tool():
    event = _event()
    line = narrative_of(event)
    assert "120 lines" not in line
    assert "read_file" not in line
    assert event.detail not in line


def test_detail_stands_only_on_the_detail_road():
    book = load_work_view()
    marker = "24 passed"
    assert marker not in format_stream(book)
    assert marker not in format_work_view_screen(book)
    assert marker not in format_panel(book)
    assert marker not in format_verdict(book)
    assert marker not in panel_plain_words(book)
    assert marker not in verdict_plain_words(book)
    event = book.events[4]
    assert marker not in format_event(event)
    assert marker in detail_of(event)
    assert marker in format_event_detail(event)
    assert marker in format_stream(book, detail=True)
    assert marker in format_work_view_screen(book, detail=True)
    assert marker in detail_plain_words(event)


# ---------------------------------------------------------------------
# Composition: kinds judged from shipped tool calls.
# ---------------------------------------------------------------------


def test_kind_for_tool_judges_the_shipped_tools():
    assert kind_for_tool("read_file") == "reading"
    assert kind_for_tool("write_file") == "writing"
    assert kind_for_tool("grep_search") == "searching"
    assert kind_for_tool("run_command", "git status") == (
        "running-command")
    assert kind_for_tool(
        "run_command", "tests/test_work_view.py",
        "pytest tests/test_work_view.py - 24 passed") == (
        "running-tests")
    with pytest.raises(ValueError):
        kind_for_tool("dance_tool")


def test_event_from_tool_call_derives_its_kind():
    event = event_from_tool_call(
        "replace_file_content", target="auth.py",
        detail="one hunk replaced.", seq=7, occurred_on=ON,
        origin_session="session-test")
    assert event.kind == "editing"
    assert narrative_of(event) == "edited `auth.py`"
    with pytest.raises(ValueError):
        event_from_tool_call(
            "replace_file_content", target="auth.py",
            detail="one hunk replaced.", seq=8,
            kind="reading")


def test_inspect_action_source_names_what_a_piece_is():
    found = inspect_action_source({
        "tool": "read_file", "path": "auth.py",
        "result": "120 lines"})
    assert found["kind"] == "reading"
    assert found["tool"] == "read_file"
    assert inspect_action_source({"words": "x"})["kind"] is None
    assert inspect_action_source("nope")["kind"] is None
    unknown = inspect_action_source({"tool": "dance_tool"})
    assert unknown["kind"] is None
    assert "no kind stands judged" in unknown["reason"]


# ---------------------------------------------------------------------
# The panel and the verdict: derived, never chosen.
# ---------------------------------------------------------------------


def _mixed_book():
    return _book([
        _event(),
        _event(event_id="event-two", seq=2, kind="editing",
               tool="replace_file_content", state="started",
               target="session.py",
               detail="replace_file_content session.py."),
        _event(event_id="event-three", seq=3,
               kind="running-tests", tool="run_command",
               target="the test suite", state="failed",
               detail="run_command pytest - 2 failed."),
    ])


def test_panel_is_derived_from_the_whole_book():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.total_events == 3
    assert (panel.total_done, panel.total_started,
            panel.total_failed) == (1, 1, 1)
    assert panel.distinct_targets == 3
    assert panel.current_event_id == "event-two"
    assert [row.event_id for row in panel.rows] == [
        "event-test", "event-two", "event-three"]
    assert panel.rows[1].narrative == "editing `session.py`\u2026"
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "reading": 1, "editing": 1, "running-tests": 1}
    for row in panel.rows:
        assert "detail" not in row.to_record()


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = _mixed_book()
    stored = derive_panel(book).to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["total_done"] = 3
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    stored = derive_panel(book).to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["rows"][0]["narrative"] = "a chosen line"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    panel = build_panel(derive_panel(book).to_record(), book)
    assert panel.total_events == 3


def test_row_is_judged_against_its_event():
    event = _event()
    row = build_row(event=event)
    assert row.narrative == "read `auth.py`"
    assert validate_row(row.to_record(), event) == row
    bad = row.to_record()
    bad["narrative"] = "a chosen line"
    with pytest.raises(ValueError):
        validate_row(bad, event)


def test_verdict_bands_and_the_working_example():
    book = load_work_view()
    verdict = derive_verdict(book)
    assert verdict.verdict == "working"
    assert verdict.total_started == 1
    calm = derive_verdict(_book())
    assert calm.verdict == "calm"
    troubled = derive_verdict(_mixed_book())
    assert troubled.verdict == "troubled"
    assert troubled.total_failed == 1
    assert build_verdict(troubled.to_record(), _mixed_book()) == troubled
    with pytest.raises(ValueError):
        WorkVerdict(
            total_events=1, total_done=1, total_started=0,
            total_failed=0, distinct_targets=1,
            earliest_on=ON, latest_on=ON, verdict="troubled")
    with pytest.raises(ValueError):
        validate_verdict(troubled.to_record(), _book())


# ---------------------------------------------------------------------
# The book, the file loader and the registry.
# ---------------------------------------------------------------------


def test_book_laws_one_event_per_id_and_sequence_in_order():
    with pytest.raises(ValueError):
        _book([_event(), _event(seq=2)])
    with pytest.raises(ValueError):
        _book([_event(), _event(event_id="event-two")])
    with pytest.raises(ValueError):
        _book([_event(seq=2), _event(event_id="event-two", seq=1)])
    book = _book()
    assert book.event_for("event-test").target == "auth.py"
    with pytest.raises(KeyError):
        book.event_for("event-nope")
    assert total_events(book) == 1
    assert events_of_kind(book, "reading") == book.events
    assert events_of_kind(book, "editing") == ()


def test_book_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "work_view.yaml").read_text(encoding="utf-8")
    path = tmp_path / "work_view.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_work_view_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_events(book) == 6


def test_registry_holds_events_one_by_one():
    registry = WorkRegistry()
    held = registry.register_event(_event(event_id=None))
    assert held.event_id == "event-1"
    registry.register_event(_event(event_id="event-two", seq=2))
    assert registry.latest_event().event_id == "event-two"
    assert registry.detail_for("event-two") == DETAIL
    assert registry.book().title == "Work View"
    assert registry.panel().total_events == 2
    assert registry.verdict().verdict == "calm"
    with pytest.raises(ValueError):
        registry.register_event(_event(event_id="event-two", seq=3))
    with pytest.raises(ValueError):
        registry.register_event(_event(event_id="event-three", seq=2))
    with pytest.raises(KeyError):
        registry.get_event("event-nope")


def test_registry_register_book_and_refusals():
    registry = WorkRegistry()
    book = registry.register_book(_mixed_book())
    assert total_events(book) == 3
    assert registry.title() == "A test work book"
    with pytest.raises(ValueError):
        registry.register_book(_book())
    other = WorkRegistry(_book())
    assert other.latest_event().event_id == "event-test"


# ---------------------------------------------------------------------
# News, plain words, formatters and the grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    event = _event()
    news = event_record(event)
    assert news["news"] is True
    assert "read `auth.py`" in news["headline"]
    panel_news = panel_record(derive_panel(_mixed_book()))
    assert "Work panel" in panel_news["headline"]
    verdict_news = verdict_record(derive_verdict(_mixed_book()))
    assert "troubled" in verdict_news["headline"]
    book_news = book_record(_mixed_book())
    assert book_news["event_count"] == 3


def test_formatters_and_screen():
    book = load_work_view()
    text = format_event(book.events[0])
    assert "event-screens-read" in text
    assert "held back" in text
    assert "Panel in Streaming Work View" in format_panel(book)
    assert format_verdict(book).startswith(
        "Verdict in Streaming Work View")
    assert "working" in format_verdict(book)
    listed = format_stream(book, kind="reading")
    assert "event-screens-read" in listed
    assert "event-charter-tests-run" not in listed
    screen = format_work_view_screen()
    assert "Streaming Work View (M-172)" in screen
    assert "event-verdicts-checked" in screen
    assert "one keystroke away" in plain_words(book.events[0])
    assert "Actions, in stream order" in panel_plain_words(book)
    assert "working" in verdict_plain_words(book)


def test_parse_work_view_args_grammar():
    assert parse_work_view_args("") == ("show", None)
    assert parse_work_view_args(None) == ("show", None)
    assert parse_work_view_args("show") == ("show", None)
    assert parse_work_view_args("list") == ("show", None)
    assert parse_work_view_args("event event-x") == (
        "event", "event-x")
    assert parse_work_view_args("detail") == ("detail", None)
    assert parse_work_view_args("detail event-x") == (
        "detail", "event-x")
    assert parse_work_view_args("kind tests") == (
        "kind", "running-tests")
    assert parse_work_view_args("panel") == ("panel", None)
    assert parse_work_view_args("verdict") == ("verdict", None)
    for bad in ("event", "kind whenever", "panel now",
                "dance", 42):
        with pytest.raises(ValueError):
            parse_work_view_args(bad)


def test_pure_layer_imports_no_agent_or_ui():
    text = (ROOT / "mythic_agent" / "core"
            / "work_view.py").read_text(encoding="utf-8")
    assert "mythic_agent.agents" not in text
    assert "import textual" not in text
    assert "from ..agents" not in text


# -- agent layer -----------------------------------------------------------
#
# M-172 agent layer: the agent holds a
# WorkRegistry for the session (session state
# only, no new setting), events are held by being
# registered - published as their event_record
# session news through the checkpoint road, deduped
# per shape - the report road renders the held
# book (or the shipped example when unheld)
# through the pure formatters, a streaming road
# raises an event over a shipped tool action by
# import (its kind derived from the tool's own
# name, its words crossing only into the detail
# the event holds back), the detail road speaks
# one event's held detail only when it is asked
# for by name, and the /workview surface rides
# both roads on the pure parser + formatters.
# Status, get, detail, panel, verdict and report
# reads register and publish nothing, answer from
# the held registry first and from the shipped
# example only while nothing is held - a held
# event never falls back to the example. The
# panel and the verdict derive at call time from
# the whole book, never held. This layer sends
# nothing, posts nothing, schedules nothing,
# calls no model, persists nothing beyond the
# session journal news, runs no tool and streams
# nothing live - an event held here is a record
# of work, never the work itself, and the slice
# board is M-173's road, so the screen is where
# the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _work_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_work_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "work_view.yaml").read_text(encoding="utf-8")
    path = tmp_path / "work_view.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestWorkViewAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.work_view_status()
        assert status["events"] == []
        assert status["book"] is None
        assert status["work_view"]["title"] == EXAMPLE_TITLE
        assert len(status["work_view"]["events"]) == 6
        assert status["panel"]["total_events"] == 6
        assert status["panel"]["total_started"] == 1
        assert status["panel"]["current_event_id"] == (
            "event-verdicts-checked")
        assert status["panels"][0]["panel_id"] == "panel-m171-boundary"
        assert status["book_record"]["event_count"] == 6
        assert status["verdict"]["verdict"] == "working"
        assert "checking the eight screen verdicts" in (
            status["plain_words"])
        assert "Streaming Work View (M-172)" in status["screen"]
        assert "24 passed" not in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._work_view_registry()
        assert agent._work_view_registry() is first
        assert agent._work_view_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.work_view_status()
        agent.get_work_view_event("event-screens-read")
        assert "24 passed" in agent.work_view_event_detail(
            "event-charter-tests-run")
        assert [e.event_id for e in agent.work_view_events_for_kind(
            "reading")] == ["event-screens-read"]
        agent.work_view_panel()
        agent.work_view_verdict()
        agent.report_work_view()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("work_view")] == []
        with pytest.raises(KeyError):
            agent.get_work_view_event("event-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_work_view_event(_event())
        status = agent.work_view_status()
        assert [item["event_id"] for item in status["events"]] == [
            "event-test"]
        assert status["book"]["title"] == "Work View"
        assert status["panel"]["total_events"] == 1
        assert status["verdict"]["verdict"] == "calm"

    def test_held_event_never_falls_back_to_the_example(
            self, agent):
        agent.register_work_view_event(_event())
        with pytest.raises(KeyError):
            agent.get_work_view_event("event-screens-read")
        event = agent.get_work_view_event("event-test")
        assert event.target == "auth.py"
        assert agent.work_view_book().title == "Work View"


class TestWorkViewAgentHolding:
    def test_register_event_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_work_view_event(_event())
        assert outcome["event"]["event_id"] == "event-test"
        assert outcome["record_news"]["news"] is True
        agent.register_work_view_event(_event(
            event_id="event-two", seq=2, kind="editing",
            tool="replace_file_content"))
        events = _work_events(store, session_id, "work_view_event")
        assert len(events) == 2
        agent.close()

    def test_duplicate_event_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_work_view_event(_event())
        with pytest.raises(ValueError):
            agent.register_work_view_event(_event())
        with pytest.raises(ValueError):
            agent.register_work_view_event(_event(seq=2))
        events = _work_events(store, session_id, "work_view_event")
        assert len(events) == 1
        agent.close()

    def test_stream_road_derives_kind_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.stream_work_view_action(
            "read_file", target="auth.py",
            detail="read_file auth.py - 120 lines.",
            origin_session="session-test")
        assert outcome["kind"] == "reading"
        assert outcome["narrative"] == "read `auth.py`"
        assert outcome["event"]["seq"] == 1
        second = agent.stream_work_view_action(
            "run_command", target="tests/test_work_view.py",
            detail="pytest tests/test_work_view.py - 49 passed",
            origin_session="session-test")
        assert second["kind"] == "running-tests"
        assert second["event"]["seq"] == 2
        assert len(_work_events(
            store, session_id, "work_view_event")) == 2
        assert len(_work_events(
            store, session_id, "work_view_panel")) == 2
        assert len(_work_events(
            store, session_id, "work_view_verdict")) == 2
        agent.close()

    def test_stream_road_unknown_tool_refuses(self, agent):
        with pytest.raises(ValueError):
            agent.stream_work_view_action(
                "dance_tool", target="auth.py", detail="x.")
        assert agent._work_view_registry().list_events() == ()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_work_view_book(_mixed_book())
        assert outcome["count"] == 3
        assert [e["event_id"] for e in outcome["events"]] == [
            "event-test", "event-two", "event-three"]
        events = _work_events(store, session_id, "work_view_event")
        assert [e["event_id"] for e in events] == [
            "event-test", "event-two", "event-three"]
        assert len(_work_events(
            store, session_id, "work_view_panel")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_work_view_book()
        assert outcome["count"] == 6
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_work_events(
            store, session_id, "work_view_event")) == 6
        with pytest.raises(ValueError):
            agent.record_work_view_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_work_book(tmp_path)
        book = load_work_view_file(path)
        outcome = agent.record_work_view_book(book)
        assert outcome["count"] == 6
        assert agent.work_view_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_work_view()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["events"]) == 6
        assert report["verdict"]["verdict"] == "working"
        agent.register_work_view_event(_event())
        report = agent.report_work_view()
        assert [e["event_id"] for e in report["events"]] == [
            "event-test"]
        assert "read `auth.py`" in report["stream_text"]
        assert DETAIL not in report["stream_text"]

    def test_holding_and_streaming_run_no_tool(self, agent):
        for name in (
                "run_work_view_tool", "execute_work_view",
                "stream_live_tools", "work_view_board",
                "persist_work_view", "send_work_view",
                "schedule_work_view", "sync_work_view_event",
                "apply_work_view", "open_live_stream"):
            assert not hasattr(agent, name), name
        agent.register_work_view_event(_event())
        agent.stream_work_view_action(
            "read_file", target="session.py",
            detail="read_file session.py.",
            origin_session="session-test")
        registry = agent._work_view_registry()
        assert [e.event_id for e in registry.list_events()] == [
            "event-test", "event-1"]


class TestWorkViewTerminalSurface:
    def test_show_event_detail_kind_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/workview")
        assert "Streaming Work View (M-172)" in text
        assert "24 passed" not in text
        _, _, text = _slash(agent, "/workview event event-screens-read")
        assert "read `mythic_agent/ui/screens/chat_screen.py`" in text
        assert "held back" in text
        _, _, text = _slash(
            agent, "/workview detail event-charter-tests-run")
        assert "24 passed" in text
        _, _, text = _slash(agent, "/workview detail")
        assert "24 passed" in text
        _, _, text = _slash(agent, "/workview kind reading")
        assert "event-screens-read" in text
        assert "event-charter-tests-run" not in text
        _, _, text = _slash(agent, "/workview panel")
        assert "Panel in Streaming Work View" in text
        _, _, text = _slash(agent, "/workview verdict")
        assert "working" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/workview [show|event <event-id>"
                "|detail [<event-id>]|kind <kind>"
                "|panel|verdict]") in text
        _, _, text = _slash(agent, "/workview dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/workview event event-nope")
        assert "no event named" in text


@pytest.fixture()
def work_handler(agent, monkeypatch):
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


def _work_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestWorkViewCommand:
    def test_show_is_default(self, work_handler, agent):
        work_handler._handle_workview("")
        assert "Streaming Work View (M-172)" in (
            _work_published_text(work_handler))

    def test_event_detail_kind_panel_verdict(
            self, work_handler, agent):
        work_handler._handle_workview("event event-screens-read")
        assert "event-screens-read" in (
            _work_published_text(work_handler))
        work_handler._handle_workview(
            "detail event-charter-tests-run")
        assert "24 passed" in _work_published_text(work_handler)
        work_handler._handle_workview("kind reading")
        assert "event-kindness-searched" not in (
            _work_published_text(work_handler).split("kind")[-1])
        work_handler._handle_workview("panel")
        assert "Panel in Streaming Work View" in (
            _work_published_text(work_handler))
        work_handler._handle_workview("verdict")
        assert "working" in _work_published_text(work_handler)

    def test_bad_grammar_is_published(
            self, work_handler, agent):
        work_handler._handle_workview("dance party")
        assert USAGE in _work_published_text(work_handler)
        work_handler._handle_workview("event event-nope")
        assert "no event named" in _work_published_text(
            work_handler)


class TestChatScreenRoutingWorkView:
    def test_workview_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/workview panel", _FakeLog())
        assert calls == [("/workview", "panel")]
