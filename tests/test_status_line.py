"""M-178 Status Line of Truth - pure-layer tests.

TIER: integration

The pure layer is the status fact, held as data:
one of the six facts of the line (model, posture,
context, cost, crew, sandbox - the roadmap's own
order) with its title, its value and its detail
held whole in plain words, the panel and
keypress it opens (its kind's own, named as
data), with its provenance whole (the day it was
recorded, who recorded it, its source and the
session it was recorded in). The status line
itself is derived from the six facts - one
segment per kind in the roadmap's order - never
stored, never written by hand. A fact that is
not measured stands honestly unknown, and a kind
holding no fact stands unknown in the line. A
view is held as its own record, the one kind it
looks at or every kind at once. The panel is
derived for one held view and the verdict is
derived for the whole book under one view. The
shipped example book is held in a data file, and
a loader reads a book from any file. The M-171
charter's S-03 direction is honoured live:
gather model, context, cost and crew state into
one status line of truth, with no structural
rebuild of the screen - this slice gathers and
derives the line; it does not rebuild the live
screen. Nothing here measures anything live,
reads a live model, context, cost, crew or
sandbox state, binds a key, opens a panel,
renders a live UI, calls a model or persists
anything: a fact held here is a finding, never
the live state of the screen it describes.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.status_line import (
    FACT_KINDS,
    KEYPRESS_FOR_KIND,
    KIND_TITLES,
    PANEL_FOR_KIND,
    PLAIN_EXPLANATION,
    STATUS_LINE_RESOURCE,
    STATUS_LINE_SCHEMA,
    STATUS_LINE_SLICE,
    UNKNOWN_VALUE,
    USAGE,
    VERDICT_WORDS,
    StatusFact,
    StatusKindCount,
    StatusLineBook,
    StatusLineRegistry,
    StatusPanel,
    StatusPanelRow,
    StatusVerdict,
    StatusView,
    book_record,
    build_book,
    build_fact,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_panel,
    derive_verdict,
    fact_from_measured_value,
    fact_record,
    facts_for_kind,
    format_book,
    format_fact,
    format_line,
    format_panel,
    format_status_line_screen,
    format_verdict,
    format_view,
    inspect_fact_source,
    is_measured,
    line_of,
    load_status_line,
    load_status_line_file,
    measured_facts,
    normalize_kind,
    normalize_kind_filter,
    panel_plain_words,
    panel_record,
    parse_status_line_args,
    plain_words,
    segment_of,
    shown_facts,
    total_facts,
    unknown_fact,
    unknown_facts,
    validate_fact,
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

EXAMPLE_TITLE = "Status Line at the M-177 slice boundary"

BY = "the coordinator"
ON = "2026-11-09"


def _fact(**overrides):
    fields = {
        "fact_id": "fact-test",
        "kind": "model",
        "title": "Model",
        "value": "Test model",
        "detail": "A model fact held as data, for the tests.",
        "panel": "model panel",
        "keypress": "1",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_fact(fields)


def _fact_for_kind(kind, value="Measured value", **overrides):
    fields = {
        "fact_id": f"fact-{kind}",
        "kind": kind,
        "title": KIND_TITLES[kind],
        "value": value,
        "detail": f"A {kind} fact held as data, for the tests.",
        "panel": PANEL_FOR_KIND[kind],
        "keypress": KEYPRESS_FOR_KIND[kind],
    }
    fields.update(overrides)
    return _fact(**fields)


def _stored_fact(fact):
    stored = fact.to_record()
    for key in ("type", "slice", "segment", "measured"):
        stored.pop(key)
    return stored


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "kind_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    stored = view.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _book(facts=None, views=(), **overrides):
    fields = {
        "title": "A test status book",
        "facts": [_stored_fact(fact) for fact in (
            facts if facts is not None else [_fact()])],
        "views": [_stored_view(item) for item in views],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        facts=[
            _fact(),
            _fact_for_kind("cost", UNKNOWN_VALUE),
            _fact_for_kind("crew", "one helper"),
        ],
        views=[_view()])


def _complete_book():
    return _book(
        facts=[_fact_for_kind(kind) for kind in FACT_KINDS],
        views=[_view()])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_status_line()
    assert book.title == EXAMPLE_TITLE
    assert book.fact_ids() == (
        "fact-model", "fact-posture", "fact-context",
        "fact-cost", "fact-crew", "fact-sandbox")
    first = book.facts[0]
    assert first.kind == "model"
    assert first.value == "Example coder model"
    assert first.panel == "model panel"
    assert first.keypress == "1"
    assert book.view_ids() == ("view-all", "view-cost")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m177-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.fact_id for row in panel.rows] == [
        "fact-model", "fact-posture", "fact-context",
        "fact-cost", "fact-crew", "fact-sandbox"]
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_facts == derived.total_facts == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.kind: c.facts for c in panel.kind_counts} == {
        kind: 1 for kind in FACT_KINDS}
    assert derive_verdict(book, "view-all").verdict == "partial"
    assert derive_verdict(book, "view-cost").verdict == "empty"
    assert line_of(book) == (
        "Model: Example coder model | Posture: Trusted Forge | "
        "Context: 5,660 of 8,000 tokens | Cost so far: unknown | "
        "Crew: coordinator alone | Sandbox: on, held as data")
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / STATUS_LINE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == STATUS_LINE_SCHEMA
    assert raw["slice"] == "M-178"
    assert "line" not in raw
    assert "status_line" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-178")]
    assert slice_.title == "Status line of truth"
    assert slice_.part == 8
    assert "model" in slice_.summary
    assert "posture" in slice_.summary
    assert "context meter" in slice_.summary
    assert "cost so far" in slice_.summary
    assert "crew state" in slice_.summary
    assert "sandbox state" in slice_.summary
    assert "six facts" in slice_.summary
    assert "always visible" in slice_.summary
    assert "opening its panel on a keypress" in slice_.summary
    assert STATUS_LINE_SLICE == "M-178"


def test_charter_s03_names_m178_and_forbids_the_rebuild():
    # The M-171 charter's S-03 row owns this slice
    # beside M-172 and M-173, and its direction is
    # the law honoured here: gather the facts into
    # one status line of truth, with NO structural
    # rebuild of the live screen.
    charter = load_charter()
    chat = charter.screen("main_chat")
    assert chat.id == "S-03"
    assert chat.verdict == "repair"
    assert tuple(chat.owning_slices) == (
        "M-172", "M-173", "M-178")
    assert "status line of truth" in chat.direction
    assert "no structural rebuild" in chat.direction
    assert "model" in chat.direction
    assert "cost" in chat.direction
    assert "crew" in chat.direction


def test_closed_vocabularies():
    assert FACT_KINDS == (
        "model", "posture", "context", "cost", "crew", "sandbox")
    assert VERDICT_WORDS == ("complete", "partial", "empty")
    assert UNKNOWN_VALUE == "unknown"
    assert KIND_TITLES["cost"] == "Cost so far"
    assert PANEL_FOR_KIND["crew"] == "crew panel"
    assert KEYPRESS_FOR_KIND == {
        "model": "1", "posture": "2", "context": "3",
        "cost": "4", "crew": "5", "sandbox": "6"}
    assert normalize_kind("Meter") == "context"
    assert normalize_kind("TEAM") == "crew"
    assert normalize_kind_filter("ALL") == "all"
    assert normalize_kind_filter("sandbox-state") == "sandbox"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_kind_filter("whenever")
    assert "status line of truth" in PLAIN_EXPLANATION
    assert "no structural rebuild" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /statusline")


# ---------------------------------------------------------------------
# The fact: judged whole, its segment derived from its own fields.
# ---------------------------------------------------------------------


def test_fact_record_round_trips():
    fact = _fact()
    assert validate_fact(_stored_fact(fact)) == fact
    record = fact.to_record()
    assert record["segment"] == "Model: Test model"
    assert record["measured"] is True
    assert segment_of(fact) == "Model: Test model"
    assert fact.segment == "Model: Test model"


def test_fact_provenance_is_whole_and_required():
    fact = _fact()
    assert fact.recorded_on == ON
    assert fact.actor == BY
    assert fact.source == "test source"
    assert fact.origin_session == "session-test"
    for missing in ("recorded_on", "actor", "source",
                    "origin_session", "title", "value",
                    "detail", "panel", "keypress"):
        fields = _stored_fact(fact)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_fact(fields)


def test_fact_refuses_unknown_keys_and_derived_keys():
    fields = _stored_fact(_fact())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_fact(fields)
    # The derived-line law: a fact carries no line,
    # no segment and no status line - those are
    # derived from the facts, never stored on one.
    for derived_key in ("line", "segment", "status_line"):
        fields = _stored_fact(_fact())
        fields[derived_key] = "Model: Test model"
        with pytest.raises(ValueError):
            build_fact(fields)


def test_fact_alias_spellings_read_onto_the_fields():
    fact = build_fact({
        "id": "fact-alias", "type_of": "meter",
        "name": "Context", "reading": "1 of 2 tokens",
        "note": "An aliased fact, for the tests.",
        "opens": "context panel", "key": "3",
        "day": ON, "by": BY, "source": "test source",
        "session": "session-test"})
    assert fact.kind == "context"
    assert fact.title == "Context"
    assert fact.value == "1 of 2 tokens"
    fields = _stored_fact(_fact())
    fields["name"] = "Another title"
    with pytest.raises(ValueError):
        build_fact(fields)


def test_fact_panel_and_keypress_are_its_kinds_own():
    fact = _fact_for_kind("crew")
    assert fact.panel == "crew panel"
    assert fact.keypress == "5"
    with pytest.raises(ValueError):
        _fact(panel="cost panel")
    with pytest.raises(ValueError):
        _fact(keypress="4")
    with pytest.raises(ValueError):
        _fact_for_kind("sandbox", panel="sandbox panel",
                       keypress="1")


def test_line_is_derived_from_the_six_facts_never_stored():
    book = _mixed_book()
    assert line_of(book) == (
        "Model: Test model | Posture: unknown | "
        "Context: unknown | Cost so far: unknown | "
        "Crew: one helper | Sandbox: unknown")
    assert book.line == line_of(book)
    # A stored line on a whole book refuses too.
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / STATUS_LINE_RESOURCE
    ).read_text(encoding="utf-8"))
    raw["line"] = "Model: stored"
    with pytest.raises(ValueError):
        load_status_line(raw)
    raw.pop("line")
    raw["status_line"] = "Model: stored"
    with pytest.raises(ValueError):
        load_status_line(raw)


def test_unmeasured_facts_stay_honestly_unknown():
    fact = unknown_fact("cost", fact_id="fact-costly")
    assert fact.value == UNKNOWN_VALUE
    assert fact.measured is False
    assert is_measured(fact) is False
    assert segment_of(fact) == "Cost so far: unknown"
    assert fact.panel == "cost panel"
    assert fact.keypress == "4"
    book = _mixed_book()
    assert [f.fact_id for f in unknown_facts(book)] == ["fact-cost"]
    assert [f.fact_id for f in measured_facts(book)] == [
        "fact-test", "fact-crew"]
    shipped = load_status_line()
    cost = shipped.fact_for("fact-cost")
    assert cost.value == UNKNOWN_VALUE
    assert cost.measured is False


def test_measured_fact_from_a_value_and_unknown_refuses():
    fact = fact_from_measured_value(
        "context", "10 of 20 tokens", fact_id="fact-meter",
        detail="A measured meter, for the tests.")
    assert fact.kind == "context"
    assert fact.title == "Context"
    assert fact.measured is True
    with pytest.raises(ValueError):
        fact_from_measured_value(
            "cost", UNKNOWN_VALUE, fact_id="fact-costly",
            detail="No measurement stands here.")


def test_inspect_fact_source_names_what_a_piece_is():
    named = inspect_fact_source(
        {"kind": "team", "value": "one helper"})
    assert named["kind"] == "crew"
    assert inspect_fact_source({"kind": "crew"})["kind"] is None
    assert inspect_fact_source("nope")["kind"] is None
    bad = inspect_fact_source({"kind": "whenever", "value": "x"})
    assert bad["kind"] is None
    assert "one of" in bad["reason"]


def test_view_is_judged_whole():
    view = _view()
    assert validate_view(_stored_view(view)) == view
    assert view.kind_filter == "all"
    with pytest.raises(ValueError):
        _view(seq=0)
    fields = _stored_view(view)
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_view(fields)


def test_view_narrows_never_judges():
    book = _mixed_book()
    cost_view = _view(view_id="view-costly", kind_filter="cost")
    shown = shown_facts(book.facts, cost_view)
    assert [f.fact_id for f in shown] == ["fact-cost"]
    shown = shown_facts(book.facts, _view())
    # Shown facts stand in the roadmap's kind order,
    # whatever order they were held in.
    assert [f.kind for f in shown] == ["model", "cost", "crew"]
    assert total_facts(book) == 3
    assert [f.fact_id for f in facts_for_kind(book, "meter")] == []
    assert [f.fact_id for f in facts_for_kind(book, "crew")] == [
        "fact-crew"]


# ---------------------------------------------------------------------
# The panel and the verdict: derived, and judged against derivation.
# ---------------------------------------------------------------------


def test_panel_is_derived_for_one_view():
    book = _mixed_book()
    panel = derive_panel(book, _view())
    assert panel.total_facts == 3
    assert panel.total_shown == 3
    assert [row.kind for row in panel.rows] == [
        "model", "cost", "crew"]
    assert panel.rows[0].segment == "Model: Test model"
    assert panel.rows[1].segment == "Cost so far: unknown"
    assert panel.rows[1].measured is False
    assert {c.kind: c.facts for c in panel.kind_counts} == {
        "model": 1, "cost": 1, "crew": 1}
    cost_panel = derive_panel(
        book, _view(view_id="view-costly", kind_filter="cost"))
    assert cost_panel.total_shown == 1
    assert cost_panel.rows[0].fact_id == "fact-cost"
    assert build_panel(source=book, view=_view()) == panel


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = load_status_line()
    panel = book.panels[0]
    stored = panel.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    assert validate_panel(stored, book) == panel
    stored["rows"][0]["segment"] = "Model: another model"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    stored = panel.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    stored["total_shown"] = 5
    with pytest.raises(ValueError):
        validate_panel(stored, book)


def test_row_is_judged_against_its_fact():
    fact = _fact()
    row = build_row(fact=fact)
    assert row.segment == "Model: Test model"
    assert validate_row(row.to_record(), fact) == row
    stored = row.to_record()
    stored["segment"] = "Model: written loose"
    with pytest.raises(ValueError):
        validate_row(stored, fact)
    with pytest.raises(ValueError):
        build_row(fact=fact, segment="Model: written loose")


def test_verdict_words_complete_partial_empty():
    complete = _complete_book()
    verdict = derive_verdict(complete, _view())
    assert verdict.verdict == "complete"
    assert verdict.measured_shown == 6
    assert verdict.distinct_kinds == 6
    assert build_verdict(source=complete, view=_view()) == verdict
    mixed = _mixed_book()
    assert derive_verdict(mixed, _view()).verdict == "partial"
    unknown_only = _book(
        facts=[_fact_for_kind("cost", UNKNOWN_VALUE)],
        views=[_view()])
    assert derive_verdict(unknown_only, _view()).verdict == "empty"
    empty = _book(facts=[], views=[_view()])
    assert derive_verdict(empty, _view()).verdict == "empty"
    stored = verdict.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    assert validate_verdict(stored, complete, _view()) == verdict
    stored["verdict"] = "partial"
    with pytest.raises(ValueError):
        validate_verdict(stored)


def test_book_laws_one_fact_per_id_and_per_kind():
    with pytest.raises(ValueError):
        _book(facts=[_fact(), _fact(title="Same id, new title")])
    with pytest.raises(ValueError):
        _book(facts=[_fact(), _fact(fact_id="fact-other")])
    with pytest.raises(ValueError):
        _book(facts=[_fact()], views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(facts=[_fact()], views=[
            _view(), _view(view_id="view-two")])
    book = _mixed_book()
    assert book.fact_for("fact-test").kind == "model"
    assert book.view_for("view-test").kind_filter == "all"
    with pytest.raises(KeyError):
        book.fact_for("fact-nope")
    with pytest.raises(KeyError):
        book.view_for("view-nope")
    with pytest.raises(KeyError):
        book.panel_for("panel-nope")


def test_book_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / STATUS_LINE_RESOURCE).read_text(encoding="utf-8")
    path = tmp_path / "status_line.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_status_line_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.fact_ids() == load_status_line().fact_ids()


def test_registry_holds_facts_and_views_one_by_one():
    registry = StatusLineRegistry()
    registry.register_fact(_fact())
    registry.register_fact(_fact_for_kind("cost", UNKNOWN_VALUE))
    with pytest.raises(ValueError):
        registry.register_fact(_fact())
    with pytest.raises(ValueError):
        registry.register_fact(_fact(fact_id="fact-other"))
    view = registry.register_view(_stored_view(_view()))
    assert view.view_id == "view-test"
    assert registry.latest_view() == view
    assert registry.line() == (
        "Model: Test model | Posture: unknown | "
        "Context: unknown | Cost so far: unknown | "
        "Crew: unknown | Sandbox: unknown")
    assert registry.panel("view-test").total_shown == 2
    assert registry.verdict("view-test").verdict == "partial"
    with pytest.raises(KeyError):
        registry.get_fact("fact-nope")
    fresh = StatusLineRegistry()
    held = fresh.register_view({
        "seq": 1, "kind_filter": "all",
        "detail": "An unnamed view, for the tests.",
        "recorded_on": ON, "actor": BY,
        "source": "test source", "origin_session": "session-test"})
    assert held.view_id == "view-1"


def test_registry_register_book_and_refusals():
    registry = StatusLineRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test status book"
    assert len(book.facts) == 3
    with pytest.raises(ValueError):
        registry.register_book(_mixed_book())
    other = _book(facts=[_fact_for_kind("sandbox")],
                  title="Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_news_records_carry_headlines():
    fact = _fact()
    record = fact_record(fact)
    assert record["news"] is True
    assert record["type"] == "status_line_fact"
    assert "Model: Test model" in record["headline"]
    assert "keypress 1" in record["headline"]
    view = view_record(_view())
    assert view["type"] == "status_line_view"
    book = _mixed_book()
    panel = panel_record(derive_panel(book, _view()))
    assert panel["type"] == "status_line_panel"
    verdict = verdict_record(derive_verdict(book, _view()))
    assert verdict["type"] == "status_line_verdict"
    assert verdict["verdict"] == "partial"
    whole = book_record(book)
    assert whole["fact_count"] == 3
    assert "Model: Test model" in whole["headline"]


def test_formatters_and_screen():
    fact = _fact()
    text = format_fact(fact)
    assert "Kind: model" in text
    assert "Value: Test model" in text
    assert "model panel" in text
    assert "no live" in text
    assert "See everything" in format_view(_view())
    book = _mixed_book()
    assert "fact-cost: Cost so far: unknown" in format_book(book)
    assert "fact-test" not in format_book(book, "cost")
    assert format_line(book) == f"Status line: {line_of(book)}"
    panel_text = format_panel(book)
    assert "Panel in A test status book" in panel_text
    assert "Cost so far: unknown" in panel_text
    assert "partial" in format_verdict(book)
    screen = format_status_line_screen(load_status_line())
    assert "Status Line (M-178)" in screen
    assert "Cost so far: unknown" in screen
    assert "6 of 6 facts show" in screen
    assert "rebuilds no live screen" in screen
    assert "Test model" in plain_words(fact)
    assert "kind 'all'" in view_plain_words(_view())
    assert "Cost so far: unknown" in panel_plain_words(book)
    assert "partial" in verdict_plain_words(book)


def test_parse_status_line_args_grammar():
    assert parse_status_line_args("") == ("show", None)
    assert parse_status_line_args(None) == ("show", None)
    assert parse_status_line_args("show") == ("show", None)
    assert parse_status_line_args("list") == ("show", None)
    assert parse_status_line_args("fact fact-test") == (
        "fact", "fact-test")
    assert parse_status_line_args("view view-all") == (
        "view", "view-all")
    assert parse_status_line_args("kind meter") == ("kind", "context")
    assert parse_status_line_args("kind team") == ("kind", "crew")
    assert parse_status_line_args("line") == ("line", None)
    assert parse_status_line_args("panel") == ("panel", None)
    assert parse_status_line_args("verdict") == ("verdict", None)
    for bad in ("fact", "view", "kind whenever", "line now",
                "panel now", "dance", 42):
        with pytest.raises(ValueError):
            parse_status_line_args(bad)


def test_pure_layer_imports_no_agent_or_ui():
    text = (ROOT / "mythic_agent" / "core"
            / "status_line.py").read_text(encoding="utf-8")
    assert "mythic_agent.agents" not in text
    assert "import textual" not in text
    assert "from ..agents" not in text


# -- agent layer -----------------------------------------------------------
#
# M-178 agent layer: the agent holds a
# StatusLineRegistry for the session (session
# state only, no new setting), facts and view
# records are held by being registered - each
# judged whole before it is held - published as
# their fact_record / view_record session news
# through the checkpoint road, deduped per shape -
# a fact composed from a measured value or raised
# honestly unknown stands on the register road
# exactly as the pure layer composed it, the
# viewing road composes one view record at the
# held book's next sequence and publishes the
# derived panel and verdict news with it, whole-
# book register and record roads hold a book
# judged whole first, the report road renders the
# held book (or the shipped example when unheld)
# through the pure formatters, and the /statusline
# surface rides both roads on the pure parser +
# formatters. Status, get, kind, measured, panel,
# verdict, line and report reads register and
# publish nothing, answer from the held registry
# first and from the shipped example only while
# nothing is held - a held fact never falls back
# to the example. The panel, the verdict and the
# line derive at call time from the whole book
# under a view, never held. This layer measures
# nothing live, reads no live model, context,
# cost, crew or sandbox state, binds no key,
# opens no panel, renders no live UI, rebuilds no
# live screen, calls no model, persists nothing
# beyond the session journal news and banks
# nothing - a fact held here is a finding, never
# the live state of the screen it describes.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _line_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "status_line.yaml").read_text(encoding="utf-8")
    path = tmp_path / "status_line.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestStatusLineAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.status_line_status()
        assert status["facts"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["status_line"]["title"] == EXAMPLE_TITLE
        assert len(status["status_line"]["facts"]) == 6
        assert len(status["status_line"]["views"]) == 2
        assert status["panel"]["total_facts"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m177-boundary"
        assert status["book_record"]["fact_count"] == 6
        assert status["book_record"]["view_count"] == 2
        assert status["verdict"]["verdict"] == "partial"
        assert "Cost so far: unknown" in status["line"]
        assert "Sandbox: on, held as data" in status["plain_words"]
        assert "Status Line (M-178)" in status["screen"]
        assert "6 of 6 facts show" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._status_line_registry()
        assert agent._status_line_registry() is first
        assert agent._status_line_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.status_line_status()
        assert agent.get_status_fact(
            "fact-sandbox").kind == "sandbox"
        assert agent.get_status_view(
            "view-all").kind_filter == "all"
        assert [f.fact_id for f in agent.status_line_with_kind(
            "model")] == ["fact-model"]
        assert [f.fact_id for f in agent.status_line_with_kind(
            "meter")] == ["fact-context"]
        assert [f.fact_id for f in agent.status_line_measured()] == [
            "fact-model", "fact-posture", "fact-context",
            "fact-crew", "fact-sandbox"]
        agent.status_line_panel()
        agent.status_line_verdict()
        assert "Cost so far: unknown" in agent.status_line_line()
        agent.report_status_line()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("status_line")] == []
        with pytest.raises(KeyError):
            agent.get_status_fact("fact-nope")
        with pytest.raises(KeyError):
            agent.get_status_view("view-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_status_fact(_fact())
        status = agent.status_line_status()
        assert [fact["fact_id"] for fact in status["facts"]] == [
            "fact-test"]
        assert status["book"]["title"] == "Status Line"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert status["line"] == (
            "Model: Test model | Posture: unknown | "
            "Context: unknown | Cost so far: unknown | "
            "Crew: unknown | Sandbox: unknown")

    def test_held_fact_never_falls_back_to_the_example(
            self, agent):
        agent.register_status_fact(_fact())
        with pytest.raises(KeyError):
            agent.get_status_fact("fact-model")
        with pytest.raises(KeyError):
            agent.get_status_view("view-all")
        fact = agent.get_status_fact("fact-test")
        assert fact.title == "Model"
        assert agent.status_line_book().title == "Status Line"


class TestStatusLineAgentHolding:
    def test_register_fact_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_status_fact(_fact())
        assert outcome["fact"]["fact_id"] == "fact-test"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == "status_line_fact"
        assert "fact-test" in outcome["screen"]
        agent.register_status_fact(_fact_for_kind(
            "crew", "one helper"))
        events = _line_events(store, session_id, "status_line_fact")
        assert len(events) == 2
        agent._publish_status_line_record(fact_record(_fact()))
        agent._publish_status_line_record(
            {"type": "slice_board_card", "news": True})
        events = _line_events(store, session_id, "status_line_fact")
        assert len(events) == 2
        agent.close()

    def test_duplicate_fact_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_status_fact(_fact())
        with pytest.raises(ValueError):
            agent.register_status_fact(_fact())
        with pytest.raises(ValueError):
            agent.register_status_fact(
                _fact(fact_id="fact-other"))
        events = _line_events(store, session_id, "status_line_fact")
        assert len(events) == 1
        agent.close()

    def test_composed_facts_hold_by_the_register_road(self, agent):
        measured = fact_from_measured_value(
            "context", "10 of 20 tokens", fact_id="fact-meter",
            detail="A measured meter, for the tests.")
        outcome = agent.register_status_fact(measured)
        assert outcome["fact"]["kind"] == "context"
        unknown = unknown_fact("cost", fact_id="fact-costly")
        agent.register_status_fact(unknown)
        assert [f.fact_id for f in agent.status_line_measured()] == [
            "fact-meter"]
        assert agent.get_status_fact("fact-costly").measured is False
        assert "Cost so far: unknown" in agent.status_line_line()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_status_fact(_fact())
        outcome = agent.register_status_view(_view())
        assert outcome["view"]["view_id"] == "view-test"
        assert outcome["record_news"]["type"] == "status_line_view"
        with pytest.raises(ValueError):
            agent.register_status_view(_view(seq=2))
        with pytest.raises(ValueError):
            agent.register_status_view(
                _view(view_id="view-two"))
        assert [v.view_id for v in
                agent._status_line_registry().list_views()] == [
                    "view-test"]
        events = _line_events(store, session_id, "status_line_view")
        assert len(events) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_status_fact(_fact())
        agent.register_status_fact(_fact_for_kind(
            "cost", UNKNOWN_VALUE))
        outcome = agent.view_status_line("all")
        assert outcome["view"]["seq"] == 1
        assert outcome["view"]["view_id"] == "view-1"
        assert outcome["record_news"]["type"] == "status_line_view"
        assert outcome["panel_record"]["type"] == "status_line_panel"
        assert outcome["panel_record"]["total_shown"] == 2
        assert outcome["verdict_record"]["type"] == (
            "status_line_verdict")
        assert outcome["verdict_record"]["verdict"] == "partial"
        second = agent.view_status_line(
            "cost",
            detail="See the cost fact alone, for the tests.")
        assert second["view"]["seq"] == 2
        assert second["verdict_record"]["verdict"] == "empty"
        assert agent.status_line_verdict().verdict == "partial"
        assert len(_line_events(
            store, session_id, "status_line_view")) == 2
        assert len(_line_events(
            store, session_id, "status_line_verdict")) == 2
        agent.close()

    def test_view_road_over_an_unheld_kind_is_empty(self, agent):
        agent.register_status_fact(_fact())
        outcome = agent.view_status_line("sandbox")
        assert outcome["panel_record"]["total_shown"] == 0
        assert outcome["verdict_record"]["verdict"] == "empty"
        assert agent.status_line_panel(
            outcome["view"]["view_id"]).total_shown == 0

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_status_line_book(_mixed_book())
        assert outcome["count"] == 3
        assert [f["fact_id"] for f in outcome["facts"]] == [
            "fact-test", "fact-cost", "fact-crew"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "status_line_fact", "status_line_fact",
            "status_line_fact", "status_line_view"]
        events = _line_events(store, session_id, "status_line_fact")
        assert [e["fact_id"] for e in events] == [
            "fact-test", "fact-cost", "fact-crew"]
        assert agent.status_line_book().title == (
            "A test status book")
        with pytest.raises(ValueError):
            agent.register_status_line_book(_mixed_book())
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_status_line_book()
        assert outcome["count"] == 6
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_line_events(
            store, session_id, "status_line_fact")) == 6
        assert len(_line_events(
            store, session_id, "status_line_view")) == 2
        status = agent.status_line_status()
        assert status["panels"][0]["panel_id"] == "panel-m177-boundary"
        with pytest.raises(ValueError):
            agent.record_status_line_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_status_line_file(path)
        outcome = agent.record_status_line_book(book)
        assert outcome["count"] == 6
        assert agent.status_line_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_status_line()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["facts"]) == 6
        assert report["verdict"]["verdict"] == "partial"
        assert "fact-sandbox: Sandbox: on, held as data" in (
            report["book_text"])
        assert "Cost so far: unknown" in report["line"]
        agent.register_status_fact(_fact())
        report = agent.report_status_line()
        assert [f["fact_id"] for f in report["facts"]] == [
            "fact-test"]
        assert "fact-test: Model: Test model" in (
            report["book_text"])
        assert report["verdict"] is None

    def test_holding_and_viewing_execute_nothing(self, agent):
        for name in (
                "measure_status_line", "read_live_model",
                "read_live_context", "read_live_cost",
                "read_live_crew", "read_live_sandbox",
                "bind_status_key", "open_status_panel",
                "render_status_line_ui", "rebuild_chat_screen",
                "persist_status_line", "bank_status_line",
                "apply_status_line", "run_status_line",
                "delete_status_fact"):
            assert not hasattr(agent, name), name
        agent.register_status_fact(_fact())
        agent.view_status_line("all")
        # A view held here only ever looks: nothing was
        # measured live, no key was bound, no panel was
        # opened, no live screen was rebuilt, and the
        # line's standing lives in no setting.
        assert agent.status_line_book().title == "Status Line"
        assert agent.config.get("status_line") is None


class TestStatusLineTerminalSurface:
    def test_show_fact_view_kind_line_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/statusline")
        assert "Status Line (M-178)" in text
        _, _, text = _slash(
            agent, "/statusline fact fact-sandbox")
        assert "Kind: sandbox" in text
        assert "Value: on, held as data" in text
        _, _, text = _slash(agent, "/statusline view view-all")
        assert "kind 'all'" in text
        _, _, text = _slash(agent, "/statusline kind cost")
        assert "fact-cost" in text
        assert "fact-model" not in text
        _, _, text = _slash(agent, "/statusline line")
        assert "Cost so far: unknown" in text
        assert "Model: Example coder model" in text
        _, _, text = _slash(agent, "/statusline panel")
        assert "Panel in Status Line at the M-177 slice boundary" in (
            text)
        _, _, text = _slash(agent, "/statusline verdict")
        assert "partial" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/statusline [show|fact <fact-id>"
                "|view <view-id>|kind <kind>|line|panel|verdict]") in text
        _, _, text = _slash(agent, "/statusline dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/statusline fact fact-nope")
        assert "no fact named" in text


@pytest.fixture()
def line_handler(agent, monkeypatch):
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


def _line_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestStatusLineCommand:
    def test_show_is_default(self, line_handler, agent):
        line_handler._handle_statusline("")
        assert "Status Line (M-178)" in (
            _line_published_text(line_handler))

    def test_fact_view_line_panel_verdict(
            self, line_handler, agent):
        line_handler._handle_statusline("fact fact-sandbox")
        assert "Kind: sandbox" in (
            _line_published_text(line_handler))
        line_handler._handle_statusline("view view-all")
        assert "kind 'all'" in _line_published_text(
            line_handler)
        line_handler._handle_statusline("line")
        assert "Cost so far: unknown" in (
            _line_published_text(line_handler))
        line_handler._handle_statusline("panel")
        assert "Panel in Status Line" in (
            _line_published_text(line_handler))
        line_handler._handle_statusline("verdict")
        assert "partial" in _line_published_text(line_handler)

    def test_bad_grammar_is_published(
            self, line_handler, agent):
        line_handler._handle_statusline("dance party")
        assert USAGE in _line_published_text(line_handler)
        line_handler._handle_statusline("fact fact-nope")
        assert "no fact named" in _line_published_text(
            line_handler)


class TestChatScreenRoutingStatusLine:
    def test_statusline_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/statusline panel", _FakeLog())
        assert calls == [("/statusline", "panel")]

    def test_chat_screen_help_and_usage_name_the_line(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/statusline[/green] - show status line of truth (M-178)" in (
            text)
        assert ('"/statusline": "Usage: /statusline | '
                '/statusline fact <fact-id>') in text
