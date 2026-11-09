"""M-161 Long-session endurance - pure-layer tests.

TIER: integration

The pure layer is the endurance record itself, held
as data: one measurement of one subject under one
endurance kind (session length, journal appends,
retrieval, responsiveness, context size), carried
with its provenance whole (what was measured, the
kind, the reference it stands under, the budget set
for it against the value measured, who recorded it,
the day, and where it was read from), composed by
import from the shipped holdings it measures
(session memory, M-153, the context budget, M-147,
graph retrieval, M-152, and token thrift, M-160),
each judged by its own layer's validation, an
endurance panel derived from the whole book in
settled order, an endurance verdict derived for the
whole book - over budget reported, never passed -
the shipped example book held in a data file, and a
loader that reads a book from any file. One thing is
measured once per kind in a book. Nothing here runs
a live session, appends to a live journal, times a
live retrieval, calls a model or writes any
project's files: holding a record declares a
budget and a measurement, and that is the whole
road. A 500-turn figure stands in these tests only
as a budget and a recorded measured value.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.context_budget import load_context_budget
from mythic_agent.core.graph_retrieval import load_graph_retrieval
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.token_thrift import load_token_thrift
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.long_session_endurance import (
    ENDURANCE_KINDS,
    ENDURANCE_KIND_UNITS,
    LONG_SESSION_ENDURANCE_RESOURCE,
    LONG_SESSION_ENDURANCE_SCHEMA,
    LONG_SESSION_ENDURANCE_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    EnduranceBook,
    EnduranceKindCount,
    EndurancePanel,
    EndurancePanelRow,
    EnduranceRecord,
    EnduranceRegistry,
    EnduranceVerdict,
    book_record,
    build_book,
    build_panel,
    build_record,
    build_row,
    build_verdict,
    derive_panel,
    derive_verdict,
    endurance_from_context_item,
    endurance_from_retrieval_bundle,
    endurance_from_session_situation,
    endurance_from_thrift_record,
    endurance_record,
    endurance_records_from_session_memory,
    endurance_refs,
    format_endurance_record,
    format_endurance_records,
    format_long_session_endurance_screen,
    format_panel,
    format_verdict,
    inspect_endurance_source,
    load_long_session_endurance,
    load_long_session_endurance_file,
    normalize_endurance_kind,
    panel_plain_words,
    panel_record,
    parse_endurance_args,
    plain_words,
    total_over_budget,
    validate_book,
    validate_panel,
    validate_record,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Long-session endurance at the M-160 slice boundary"

BY = "Volmarr"
ON = "2026-11-08"


def _record(**overrides):
    fields = {
        "record_id": "endurance-test",
        "subject": "the test session, at 120 turns",
        "kind": "session-length",
        "ref": "session-test",
        "budget": 500,
        "measured": 120,
        "recorded_by": BY,
        "recorded_on": ON,
        "source": "test source",
    }
    fields.update(overrides)
    return build_record(fields)


def _stored_record(record):
    stored = record.to_record()
    for key in ("type", "slice", "unit", "verdict", "over_by"):
        stored.pop(key)
    return stored


def _stored_panel(panel):
    stored = panel.to_record()
    stored.pop("type")
    stored.pop("slice")
    for row in stored["rows"]:
        row.pop("type")
        row.pop("slice")
    return stored


def _stored_verdict(verdict):
    stored = verdict.to_record()
    stored.pop("type")
    stored.pop("slice")
    return stored


def _book(records=None, **overrides):
    fields = {
        "title": "A test endurance book",
        "records": [_stored_record(item) for item in (
            records if records is not None else [_record()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "long_session_endurance.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert LONG_SESSION_ENDURANCE_SLICE == "M-161"
    assert LONG_SESSION_ENDURANCE_SCHEMA == "mythic.long_session_endurance/1"
    assert LONG_SESSION_ENDURANCE_RESOURCE == "long_session_endurance.yaml"
    assert ENDURANCE_KINDS == (
        "session-length", "journal-append", "retrieval",
        "responsiveness", "context-size")
    assert ENDURANCE_KIND_UNITS["session-length"] == "turns"
    assert ENDURANCE_KIND_UNITS["retrieval"] == "milliseconds"
    assert ENDURANCE_KIND_UNITS["context-size"] == "tokens"
    assert "budget is set" in PLAIN_EXPLANATION
    assert "runs no live session" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /endurance")
    assert "record <record-id>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-161" in ids
    mine = road.slices[ids.index("M-161")]
    assert mine.title == "Long-session endurance"
    assert mine.part == 7
    assert "500-turn" in mine.summary
    assert "budgets set and measured" in mine.summary
    for earlier in road.slices[:ids.index("M-161")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_long_session_endurance()
    assert isinstance(book, EnduranceBook)
    assert book.title == EXAMPLE_TITLE
    assert book.record_ids() == (
        "endurance-session-m160", "endurance-journal-m160",
        "endurance-retrieval-m160", "endurance-response-m160",
        "endurance-context-m160")
    assert book.total_records == 5
    first = book.records[0]
    assert first.subject == "the M-160 token-thrift session, at 500 turns"
    assert first.kind == "session-length"
    assert first.budget == 500
    assert first.measured == 500
    assert first.verdict == "within-budget"
    assert first.recorded_by == "Volmarr"
    assert first.recorded_on == "2026-11-08"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_long_session_endurance()
    panel = book.panel_for("panel-m160-boundary")
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert [row.record_id for row in panel.rows] == [
        "endurance-session-m160", "endurance-journal-m160",
        "endurance-retrieval-m160", "endurance-response-m160",
        "endurance-context-m160"]
    assert panel.total_records == 5
    assert panel.total_within == 4
    assert panel.total_over == 1


def test_shipped_over_budget_is_reported_never_passed():
    book = load_long_session_endurance()
    record = book.record_for("endurance-response-m160")
    assert record.verdict == "over-budget"
    assert record.over_by == 140
    verdict = derive_verdict(book)
    assert verdict.verdict == "strained"
    assert verdict.worst_record_id == "endurance-response-m160"
    assert verdict.worst_over_by == 140
    assert total_over_budget(book) == 1


def test_normalizers_and_aliases():
    assert normalize_endurance_kind("Session") == "session-length"
    assert normalize_endurance_kind("TURNS") == "session-length"
    assert normalize_endurance_kind("journal") == "journal-append"
    assert normalize_endurance_kind("Append") == "journal-append"
    assert normalize_endurance_kind("search") == "retrieval"
    assert normalize_endurance_kind("GRAPH") == "retrieval"
    assert normalize_endurance_kind("response") == "responsiveness"
    assert normalize_endurance_kind("context") == "context-size"
    assert normalize_endurance_kind("Tokens") == "context-size"
    with pytest.raises(ValueError):
        normalize_endurance_kind("disk-io")


def test_record_validation_and_alias_spellings():
    record = _record()
    assert isinstance(record, EnduranceRecord)
    assert record.verdict == "within-budget"
    assert record.headroom == 380
    assert record.unit == "turns"
    aliased = build_record({
        "what": "the aliased retrieval", "kind": "search",
        "reference": "bundle-x", "budget_value": 250,
        "measured_value": 96, "by": "Volmarr",
        "day": "2026-11-08", "source": "the graph"})
    assert aliased.subject == "the aliased retrieval"
    assert aliased.kind == "retrieval"
    assert aliased.ref == "bundle-x"
    assert aliased.recorded_by == "Volmarr"
    with pytest.raises(ValueError):
        build_record({"subject": "the bare measure"})
    with pytest.raises(ValueError):
        _record(recorded_on="08/11/2026")
    with pytest.raises(ValueError):
        _record(recorded_on="2026-13-01")
    with pytest.raises(ValueError):
        _record(kind="disk-io")
    # A stored verdict refuses: the verdict is derived.
    stored = _stored_record(_record())
    stored["verdict"] = "within-budget"
    with pytest.raises(ValueError, match="unknown endurance-record keys"):
        build_record(stored)


def test_record_refuses_missing_provenance():
    fields = _stored_record(_record())
    fields.pop("recorded_by")
    with pytest.raises(ValueError, match="missing its"):
        build_record(fields)
    fields = _stored_record(_record())
    fields.pop("source")
    with pytest.raises(ValueError, match="missing its"):
        build_record(fields)
    fields = _stored_record(_record())
    fields["bogus"] = "nope"
    with pytest.raises(ValueError, match="unknown endurance-record keys"):
        build_record(fields)


def test_record_refuses_unbudgeted_or_claimed_measures():
    # A budget is set before it is measured: no budget,
    # no measurement - and a zero budget is no budget.
    with pytest.raises(ValueError, match="budget"):
        _record(budget=0)
    fields = _stored_record(_record())
    fields.pop("budget")
    with pytest.raises(ValueError, match="missing its budget"):
        build_record(fields)
    # Measuring exactly the budget is measured and
    # stands: it is within budget, and says so.
    even = _record(measured=500)
    assert even.verdict == "within-budget"
    assert even.over_by == 0
    # One over the budget is over, by exactly one.
    over = _record(measured=501)
    assert over.verdict == "over-budget"
    assert over.over_by == 1
    assert over.headroom == 0


def test_book_refuses_duplicate_record_and_duplicate_thing():
    with pytest.raises(ValueError, match="already exists"):
        _book([_record(), _record(subject="another subject")])
    # One thing is measured once per kind in a book,
    # under any second record id or subject.
    with pytest.raises(ValueError, match="measured once"):
        _book([_record(), _record(record_id="endurance-copy")])
    # The same reference under another kind is another
    # measure, and the same kind on another reference
    # is another measure: both stand.
    book = _book([_record(), _record(
        record_id="endurance-journal", subject="the test journal",
        kind="journal-append"),
        _record(record_id="endurance-other", subject="the other session",
                ref="session-other")])
    assert book.total_records == 3


def test_record_for_ref_in_book():
    book = load_long_session_endurance()
    record = book.record_for_ref("turns", "session-m160-thrift")
    assert record.record_id == "endurance-session-m160"
    assert isinstance(
        book.record_for("endurance-journal-m160"), EnduranceRecord)
    with pytest.raises(KeyError):
        book.record_for_ref("session-length", "session-nope")
    with pytest.raises(KeyError):
        book.record_for("endurance-nope")


def test_composition_from_session_situation():
    situation = load_session_memory().situations[0]
    record = endurance_from_session_situation(
        situation, budget=500, recorded_by=BY, recorded_on=ON)
    assert record.kind == "session-length"
    assert record.ref == situation.session_ref
    assert record.measured == situation.transcript_messages
    assert record.budget == 500
    # The situation's own words never cross the seam.
    blob = str(record.to_record())
    assert situation.title not in blob
    assert situation.workspace not in blob
    with pytest.raises(ValueError, match="budget"):
        endurance_from_session_situation(
            situation, budget=None, recorded_by=BY, recorded_on=ON)


def test_composition_from_context_item():
    panel = load_context_budget()
    items = [i for i in panel.items if i.item_id]
    item = items[0]
    record = endurance_from_context_item(
        item, budget=item.tokens * 2, recorded_by=BY, recorded_on=ON)
    assert record.kind == "context-size"
    assert record.ref == item.item_id
    assert record.measured == item.tokens
    blob = str(record.to_record())
    assert item.title not in blob
    assert item.reason not in blob


def test_composition_from_retrieval_bundle():
    bundle = load_graph_retrieval().bundles[0]
    record = endurance_from_retrieval_bundle(
        bundle, budget=250, measured=96, recorded_by=BY, recorded_on=ON)
    assert record.kind == "retrieval"
    assert record.ref == bundle.bundle_id
    assert record.measured == 96
    # A bundle carries no latency: naming none refuses.
    with pytest.raises(ValueError, match="measured"):
        endurance_from_retrieval_bundle(
            bundle, budget=250, measured=None,
            recorded_by=BY, recorded_on=ON)
    blob = str(record.to_record())
    assert bundle.query not in blob


def test_composition_from_thrift_record():
    thrift = load_token_thrift().records[0]
    record = endurance_from_thrift_record(
        thrift, budget=4000, recorded_by=BY, recorded_on=ON)
    assert record.kind == "context-size"
    assert record.ref == thrift.ref
    assert record.measured == thrift.actual_tokens
    blob = str(record.to_record())
    assert thrift.subject not in blob


def test_inspect_endurance_source():
    situation = load_session_memory().situations[0]
    seen = inspect_endurance_source(situation)
    assert seen == {"ref": situation.session_ref,
                    "measured": situation.transcript_messages}
    bundle = load_graph_retrieval().bundles[0]
    seen = inspect_endurance_source(bundle)
    assert seen == {"ref": bundle.bundle_id, "measured": None}
    seen = inspect_endurance_source(_record())
    assert seen == {"ref": "session-test", "measured": 120}
    with pytest.raises(ValueError, match="no shipped layer owns"):
        inspect_endurance_source(42)


def test_records_from_session_memory_plural_road():
    memory_book = load_session_memory()
    records = endurance_records_from_session_memory(
        memory_book, budget=500, recorded_by=BY, recorded_on=ON)
    assert len(records) == len(memory_book.situations)
    assert all(r.kind == "session-length" for r in records)
    assert [r.ref for r in records] == [
        s.session_ref for s in memory_book.situations]
    # No budget named refuses the whole road first.
    with pytest.raises(ValueError, match="budget"):
        endurance_records_from_session_memory(
            memory_book, budget=None, recorded_by=BY, recorded_on=ON)


def test_panel_derivation_and_order():
    book = _book([
        _record(record_id="endurance-b", subject="b session",
                ref="session-b"),
        _record(record_id="endurance-a", subject="a session",
                ref="session-a"),
        _record(record_id="endurance-j", subject="the journal",
                kind="journal-append", ref="journal-x",
                budget=50, measured=80),
    ])
    panel = derive_panel(book)
    assert isinstance(panel, EndurancePanel)
    # Kind order first (session-length before
    # journal-append), then subject, then record id.
    assert [r.record_id for r in panel.rows] == [
        "endurance-a", "endurance-b", "endurance-j"]
    assert panel.total_records == 3
    assert panel.total_within == 2
    assert panel.total_over == 1
    counts = {c.kind: c for c in panel.kind_counts}
    assert counts["session-length"].records == 2
    assert counts["journal-append"].over == 1
    assert isinstance(counts["journal-append"], EnduranceKindCount)
    assert panel.row_for("endurance-j").verdict == "over-budget"
    with pytest.raises(KeyError):
        panel.row_for("endurance-nope")


def test_panel_refuses_disagreement_and_bad_rows():
    book = load_long_session_endurance()
    panel = derive_panel(book)
    stored = _stored_panel(panel)
    assert validate_panel(stored, book) == panel
    bad = _stored_panel(panel)
    bad["total_over"] = 0
    with pytest.raises(ValueError):
        validate_panel(bad, book)
    bad = _stored_panel(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(bad, book)
    # A row whose verdict is not its figures' verdict
    # refuses at construction.
    row = _stored_panel(panel)["rows"][0]
    row["verdict"] = "over-budget"
    with pytest.raises(ValueError, match="verdict"):
        build_row(row)
    good_row = build_row(_stored_panel(panel)["rows"][0])
    assert isinstance(good_row, EndurancePanelRow)
    assert validate_row(good_row, book.records[0]) == good_row


def test_verdict_derivation_and_validation():
    book = _book([_record(), _record(
        record_id="endurance-over", subject="the long journal",
        kind="journal-append", ref="journal-x",
        budget=50, measured=95)])
    verdict = derive_verdict(book)
    assert isinstance(verdict, EnduranceVerdict)
    assert verdict.verdict == "strained"
    assert verdict.worst_record_id == "endurance-over"
    assert verdict.worst_over_by == 45
    assert validate_verdict(_stored_verdict(verdict), book) == verdict
    assert build_verdict(_stored_verdict(verdict)) == verdict
    calm = derive_verdict(_book([_record()]))
    assert calm.verdict == "enduring"
    assert calm.worst_record_id is None
    assert calm.worst_over_by == 0
    # A stored verdict claiming calm over an over
    # book refuses against its source.
    with pytest.raises(ValueError, match="disagrees"):
        validate_verdict(_stored_verdict(calm), book)
    # And a verdict whose word fights its tallies
    # refuses at construction.
    with pytest.raises(ValueError, match="verdict"):
        EnduranceVerdict(
            total_records=1, within_budget=1, over_budget=0,
            verdict="strained")


def test_book_validation_and_loader_roads(tmp_path):
    raw = _shipped_raw()
    assert validate_book(raw).title == EXAMPLE_TITLE
    assert build_book(raw).record_ids()[0] == "endurance-session-m160"
    bad = dict(raw)
    bad["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(bad)
    path = tmp_path / "endurance.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    loaded = load_long_session_endurance_file(path)
    assert loaded.title == EXAMPLE_TITLE
    with pytest.raises(FileNotFoundError):
        load_long_session_endurance_file(tmp_path / "nope.yaml")
    # The shipped file itself is the pinned example.
    assert _shipped_raw()["schema"] == LONG_SESSION_ENDURANCE_SCHEMA


def test_registry_holds_records_one_by_one():
    registry = EnduranceRegistry()
    held = registry.register_record(_record(record_id=None))
    assert held.record_id == "endurance-1"
    assert registry.latest_record() == held
    assert registry.get_record("endurance-1") == held
    assert registry.record_for_ref("turns", "session-test") == held
    with pytest.raises(ValueError, match="already exists"):
        registry.register_record(held)
    with pytest.raises(ValueError, match="measured once"):
        registry.register_record(_record(record_id="endurance-copy"))
    # A registry that has held records one by one
    # holds no book title yet: book() refuses until
    # a whole book sets one (the agent layer composes
    # the shim title, exactly as the siblings do).
    with pytest.raises(ValueError, match="no endurance book is held"):
        registry.book()
    assert registry.panel().total_records == 1
    assert registry.verdict().verdict == "enduring"
    with pytest.raises(KeyError):
        registry.get_record("endurance-nope")


def test_registry_register_book_and_title_law():
    registry = EnduranceRegistry()
    book = _book()
    held_book = registry.register_book(book)
    assert held_book.title == "A test endurance book"
    assert registry.list_records()[0].record_id == "endurance-test"
    with pytest.raises(ValueError):
        registry.register_book(book)
    other = _book([_record(record_id="endurance-z", ref="session-z")],
                  title="Another title")
    with pytest.raises(ValueError, match="different title"):
        registry.register_book(other)
    fresh = EnduranceRegistry(load_long_session_endurance())
    assert fresh.book().total_records == 5


def test_news_records_and_plain_words():
    record = _record()
    news = endurance_record(record)
    assert news["type"] == "long_session_endurance_record"
    assert news["news"] is True
    assert "within-budget" in news["headline"]
    book = load_long_session_endurance()
    panel_news = panel_record(derive_panel(book), book)
    assert panel_news["type"] == "long_session_endurance_panel"
    assert "1 over budget" in panel_news["headline"]
    verdict_news = verdict_record(derive_verdict(book), book)
    assert verdict_news["type"] == "long_session_endurance_verdict"
    assert "strained" in verdict_news["headline"]
    whole = book_record(book)
    assert whole["type"] == "long_session_endurance_book"
    assert whole["record_count"] == 5
    words = plain_words(book.records[3])
    assert "over-budget" in words
    assert "Volmarr" in words
    panel_words = panel_plain_words(book)
    assert "endurance-response-m160" in panel_words
    assert "never silently passed" in panel_words
    verdict_words = verdict_plain_words(book)
    assert "strained" in verdict_words
    assert "endurance-response-m160" in verdict_words


def test_refs_and_totals_surface():
    book = load_long_session_endurance()
    refs = endurance_refs(book)
    assert refs[0] == ("session-length", "session-m160-thrift")
    assert ("responsiveness", "session-m160-thrift") in refs
    assert len(refs) == 5


def test_formatters_and_screen():
    book = load_long_session_endurance()
    block = format_endurance_record(book.records[3])
    assert "over-budget" in block
    assert "by 140" in block
    listing = format_endurance_records(book)
    assert "endurance-session-m160" in listing
    only = format_endurance_records(book, "journal")
    assert "endurance-journal-m160" in only
    assert "endurance-session-m160" not in only
    panel_text = format_panel(book)
    assert "Endurance panel in" in panel_text
    assert "never silently passed" in panel_text
    verdict_text = format_verdict(book)
    assert "strained" in verdict_text
    screen = format_long_session_endurance_screen(book)
    assert "Long-Session Endurance (M-161)" in screen
    assert USAGE in screen
    default_screen = format_long_session_endurance_screen()
    assert "endurance-session-m160" in default_screen


def test_parse_endurance_args():
    assert parse_endurance_args("") == ("show", None)
    assert parse_endurance_args("show") == ("show", None)
    assert parse_endurance_args("list") == ("show", None)
    assert parse_endurance_args(
        "record endurance-session-m160") == (
            "record", "endurance-session-m160")
    assert parse_endurance_args("kind turns") == (
        "kind", "session-length")
    assert parse_endurance_args("panel") == ("panel", None)
    assert parse_endurance_args("verdict") == ("verdict", None)
    with pytest.raises(ValueError, match="Usage"):
        parse_endurance_args("dance party")
    with pytest.raises(ValueError):
        parse_endurance_args("kind disk-io")
    with pytest.raises(ValueError):
        parse_endurance_args(42)


# -- agent layer -----------------------------------------------------------
#
# M-161 agent layer: the agent holds an
# EnduranceRegistry for the session (session state
# only, no new setting), records are held by being
# registered - published as their endurance_record
# session news with the derived panel_record and
# verdict_record, through the checkpoint road, deduped
# per shape - the report road renders the held book
# (or the shipped example when unheld) through the
# pure formatters, an endurance road reads the
# session's session-memory book onto endurance
# records and holds them (mutating no live memory),
# and the /endurance surface rides both roads on the
# pure parser + formatters. Status, get, panel,
# verdict and report reads register and publish
# nothing, answer from the held registry first and
# from the shipped example only while nothing is
# held - a held session never falls back to the
# example. The panel and the verdict derive at call
# time from the whole book, never held. This layer
# runs no live session, appends to no live journal,
# times no live retrieval, calls no model and
# persists nothing beyond the session journal news,
# and there is no Part VIII board yet, so the screen
# is where the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _endurance_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_endurance_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "long_session_endurance.yaml").read_text(encoding="utf-8")
    path = tmp_path / "long_session_endurance.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestEnduranceAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.long_session_endurance_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["enduring"]["title"] == EXAMPLE_TITLE
        assert len(status["enduring"]["records"]) == 5
        assert status["panel"]["total_records"] == 5
        assert status["panel"]["total_over"] == 1
        assert status["panels"][0]["panel_id"] == "panel-m160-boundary"
        assert status["book_record"]["record_count"] == 5
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["worst_record_id"] == (
            "endurance-response-m160")
        assert status["verdict"]["worst_over_by"] == 140
        assert "Long-Session Endurance (M-161)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._long_session_endurance_registry()
        assert agent._long_session_endurance_registry() is first
        assert agent._long_session_endurance_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.long_session_endurance_status()
        agent.get_endurance_record("endurance-response-m160")
        agent.long_session_endurance_panel()
        agent.long_session_endurance_verdict()
        agent.report_long_session_endurance()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("long_session_endurance")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_endurance_record("endurance-nope")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_endurance_record(_record())
        status = agent.long_session_endurance_status()
        assert [item["record_id"] for item in status["records"]] == [
            "endurance-test"]
        assert status["book"]["title"] == "Long-session endurance"
        assert status["panel"]["total_records"] == 1
        assert status["verdict"]["verdict"] == "enduring"

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_endurance_record(_record())
        with pytest.raises(KeyError):
            agent.get_endurance_record("endurance-response-m160")
        record = agent.get_endurance_record("endurance-test")
        assert record.subject == "the test session, at 120 turns"
        assert agent.long_session_endurance_book().title == (
            "Long-session endurance")


class TestEnduranceAgentHolding:
    def test_register_record_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_endurance_record(_record())
        assert outcome["record"]["record_id"] == "endurance-test"
        assert outcome["record_news"]["type"] == (
            "long_session_endurance_record")
        events = _endurance_events(
            store, session_id, "long_session_endurance_record")
        assert len(events) == 1
        assert events[0]["record_id"] == "endurance-test"
        agent._publish_endurance_record(outcome["record_news"])
        assert len(_endurance_events(
            store, session_id, "long_session_endurance_record")) == 1
        agent._publish_endurance_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_endurance_record(
            book_record(load_long_session_endurance()))
        for kind in ("mentions_mention", "long_session_endurance_book"):
            assert _endurance_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_endurance_record(_record())
        with pytest.raises(ValueError):
            agent.register_endurance_record(_record())
        with pytest.raises(ValueError):
            agent.register_endurance_record(
                _record(record_id="endurance-copy"))
        assert len(_endurance_events(
            store, session_id, "long_session_endurance_record")) == 1
        agent.close()

    def test_endurance_from_session_memory_carries_refs_only(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        memory_book = agent.session_memory_book()
        situations = list(memory_book.situations)
        expected = len(situations)
        outcome = agent.endurance_from_session_memory(
            budget=500, recorded_by="Volmarr",
            recorded_on="2026-11-08")
        assert outcome["count"] == expected
        assert outcome["total_over"] == 0
        assert outcome["records"][0]["ref"] == (
            situations[0].session_ref)
        assert outcome["records"][0]["measured"] == (
            situations[0].transcript_messages)
        assert outcome["records"][0]["kind"] == "session-length"
        events = _endurance_events(
            store, session_id, "long_session_endurance_record")
        assert len(events) == expected
        assert len(_endurance_events(
            store, session_id, "long_session_endurance_panel")) == 1
        assert len(_endurance_events(
            store, session_id, "long_session_endurance_verdict")) == 1
        blob = str(events) + str(outcome["records"])
        for situation in situations:
            assert situation.title not in blob
            assert situation.workspace not in blob
        # Measuring mutated no live memory: the
        # session's memory book stands whole.
        assert agent.session_memory_book().situations == (
            memory_book.situations)
        assert agent.long_session_endurance_panel().total_records == (
            expected)
        with pytest.raises(ValueError):
            agent.endurance_from_session_memory(
                budget=500, recorded_by="Volmarr",
                recorded_on="2026-11-08")
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_endurance_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["records_news"]] == [
            "long_session_endurance_record"]
        assert agent.long_session_endurance_book().title == (
            "A test endurance book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_endurance_book(load_long_session_endurance())
        with pytest.raises(ValueError):
            agent.register_endurance_book(load_long_session_endurance())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_endurance_book()
        assert outcome["count"] == 5
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_endurance_events(
            store, session_id, "long_session_endurance_record")) == 5
        assert len(_endurance_events(
            store, session_id, "long_session_endurance_panel")) == 1
        assert agent.long_session_endurance_book().panels[0].panel_id == (
            "panel-m160-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_endurance_book()
        with pytest.raises(ValueError):
            agent.record_endurance_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_endurance_book(tmp_path)
        book = load_long_session_endurance_file(path)
        outcome = agent.record_endurance_book(book)
        assert outcome["count"] == 5
        assert agent.get_endurance_record(
            "endurance-retrieval-m160").kind == "retrieval"

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_long_session_endurance()
        assert report["book"]["record_count"] == 5
        assert "endurance-session-m160" in report["records_text"]
        assert "Endurance panel in Long-session endurance" in (
            report["panel_text"])
        assert "strained" in report["verdict_text"]
        assert "endurance-response-m160" in report["verdict_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_endurance_record(_record())
        report = agent.report_long_session_endurance()
        assert report["book"]["title"] == "Long-session endurance"
        assert "endurance-session-m160" not in report["records_text"]
        assert "endurance-test" in report["records_text"]
        assert "enduring" in report["verdict_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_long_session_endurance()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("long_session_endurance")] == []
        agent.close()

    def test_no_live_session_journal_or_persist_road(
            self, agent, tmp_path):
        # This layer holds endurance as data: it runs
        # no live session, appends to no live journal,
        # times no live retrieval, calls no model and
        # persists nothing - and there is no Part VIII
        # board yet. Holding, recording or measuring
        # changes no workspace file and no built
        # context.
        assert not hasattr(agent, "apply_long_session_endurance")
        assert not hasattr(agent, "run_long_session_endurance")
        assert not hasattr(agent, "persist_long_session_endurance")
        assert not hasattr(agent, "long_session_endurance_board")
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
        agent.register_endurance_record(_record())
        agent.record_endurance_book()
        agent.endurance_from_session_memory(
            budget=500, recorded_by="Volmarr",
            recorded_on="2026-11-08")
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestEnduranceTerminalSurface:
    def test_show_record_kind_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/endurance")
        assert "Long-Session Endurance (M-161)" in text
        _, _, text = _slash(
            agent, "/endurance record endurance-journal-m160")
        assert "journal-session-store" in text
        _, _, text = _slash(agent, "/endurance kind retrieval")
        assert "endurance-retrieval-m160" in text
        assert "endurance-session-m160" not in text
        _, _, text = _slash(agent, "/endurance panel")
        assert "Endurance panel in Long-session endurance" in text
        _, _, text = _slash(agent, "/endurance verdict")
        assert "strained" in text
        assert "endurance-response-m160" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/endurance [show|record <record-id>"
                "|kind <kind>|panel|verdict]") in text
        _, _, text = _slash(agent, "/endurance dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/endurance record endurance-nope")
        assert "no endurance record in the book" in text


@pytest.fixture()
def endurance_handler(agent, monkeypatch):
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


def _endurance_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestEnduranceCommand:
    def test_show_is_default(self, endurance_handler, agent):
        endurance_handler._handle_endurance("")
        assert "Long-Session Endurance (M-161)" in (
            _endurance_published_text(endurance_handler))

    def test_record_kind_panel_verdict(self, endurance_handler, agent):
        endurance_handler._handle_endurance(
            "record endurance-journal-m160")
        assert "journal-session-store" in (
            _endurance_published_text(endurance_handler))
        endurance_handler._handle_endurance("kind retrieval")
        assert "endurance-retrieval-m160" in (
            _endurance_published_text(endurance_handler))
        endurance_handler._handle_endurance("panel")
        assert "Endurance panel in Long-session endurance" in (
            _endurance_published_text(endurance_handler))
        endurance_handler._handle_endurance("verdict")
        assert "strained" in (
            _endurance_published_text(endurance_handler))

    def test_bad_grammar_is_published(self, endurance_handler, agent):
        endurance_handler._handle_endurance("dance party")
        assert USAGE in _endurance_published_text(endurance_handler)


class TestChatScreenRoutingEndurance:
    def test_endurance_routes_as_system_command(self, monkeypatch):
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
            "/endurance record endurance-journal-m160", _FakeLog())
        assert calls == [("/endurance",
                          "record endurance-journal-m160")]
